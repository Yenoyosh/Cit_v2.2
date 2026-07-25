from __future__ import annotations

import ipaddress
import json
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Any

DISCOVERY_PORT = 50100
CONTROL_PORT = 50110
MAGIC = "CIT_DISCOVER_V1"
REPLY = "CIT_PROJECT_V2"
OLD_REPLY = "CIT_PROJECT_V1"


@dataclass
class FoundProject:
    ip: str
    project: str
    host: str
    port: int
    project_id: str = ""


def _local_ipv4_candidates() -> list[str]:
    ips: set[str] = set()
    try:
        host = socket.gethostname()
        for info in socket.getaddrinfo(host, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if not ip.startswith("127."):
            ips.add(ip)
        s.close()
    except Exception:
        pass
    return sorted(ips)


def _subnet_hosts_for_local_ips(limit_per_subnet: int = 254) -> list[str]:
    hosts: list[str] = []
    seen: set[str] = set()
    for ip in _local_ipv4_candidates():
        try:
            net = ipaddress.ip_network(ip + "/24", strict=False)
            count = 0
            for host in net.hosts():
                text = str(host)
                if text == ip or text in seen:
                    continue
                seen.add(text)
                hosts.append(text)
                count += 1
                if count >= limit_per_subnet:
                    break
        except Exception:
            continue
    return hosts


def start_discovery_responder(get_projects: Callable[[], Any], stop: threading.Event) -> threading.Thread:
    def run() -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", DISCOVERY_PORT))
        except OSError:
            return
        sock.settimeout(0.5)
        while not stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                if data.decode("utf-8", "ignore") != MAGIC:
                    continue
                projects = get_projects()
                payload = {
                    "type": REPLY,
                    "host": socket.gethostname(),
                    "port": CONTROL_PORT,
                    "projects": projects,
                }
                sock.sendto(json.dumps(payload).encode("utf-8"), addr)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue
        sock.close()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


def _parse_reply(data: bytes, addr_ip: str) -> list[FoundProject]:
    out: list[FoundProject] = []
    payload = json.loads(data.decode("utf-8"))
    if payload.get("type") not in {REPLY, OLD_REPLY}:
        return out
    for raw_project in payload.get("projects", []):
        if isinstance(raw_project, dict):
            name = str(raw_project.get("name", ""))
            pid = str(raw_project.get("id", ""))
        else:
            name = str(raw_project)
            pid = ""
        if not name:
            continue
        out.append(FoundProject(addr_ip, name, str(payload.get("host", addr_ip)), int(payload.get("port", CONTROL_PORT)), pid))
    return out


def _scan_udp_targets(targets: list[str], timeout: float) -> list[FoundProject]:
    found: dict[tuple[str, str, str], FoundProject] = {}
    if not targets:
        return []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.12)
    for target in targets:
        try:
            sock.sendto(MAGIC.encode("utf-8"), (target, DISCOVERY_PORT))
        except OSError:
            continue
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(65535)
            for fp in _parse_reply(data, addr[0]):
                found[(fp.ip, fp.project, fp.project_id)] = fp
        except socket.timeout:
            continue
        except Exception:
            continue
    sock.close()
    return sorted(found.values(), key=lambda x: (x.ip, x.project))


def scan_projects_at(ip: str, timeout: float = 2.0) -> list[FoundProject]:
    """Scan one specific IPv4 address for Cit projects."""
    ip = ip.strip()
    if not ip:
        return []
    return _scan_udp_targets([ip], timeout)


def scan_projects(timeout: float = 2.8) -> list[FoundProject]:
    """Reliable LAN scan.

    Cit first tries classic broadcast. Because Windows Firewall, guest Wi-Fi and
    some routers often drop broadcast packets, it then also scans the local /24
    subnet with direct UDP probes in parallel. Direct IP scan is still available
    for manual troubleshooting.
    """
    found: dict[tuple[str, str, str], FoundProject] = {}

    # Fast broadcast pass.
    for target in ["255.255.255.255"]:
        for fp in _scan_udp_targets([target], min(1.1, timeout)):
            found[(fp.ip, fp.project, fp.project_id)] = fp

    # Direct local-subnet sweep. Split into chunks to keep the UI responsive and
    # avoid waiting on 254 sequential timeouts.
    hosts = _subnet_hosts_for_local_ips()
    if hosts:
        def probe(ip: str) -> list[FoundProject]:
            return scan_projects_at(ip, timeout=0.45)
        with ThreadPoolExecutor(max_workers=64) as ex:
            futures = [ex.submit(probe, ip) for ip in hosts]
            deadline = time.time() + max(1.4, timeout)
            for fut in as_completed(futures, timeout=max(1.8, timeout + 0.6)):
                try:
                    for fp in fut.result(timeout=0):
                        found[(fp.ip, fp.project, fp.project_id)] = fp
                except Exception:
                    pass
                if time.time() > deadline:
                    break
    return sorted(found.values(), key=lambda x: (x.ip, x.project))
