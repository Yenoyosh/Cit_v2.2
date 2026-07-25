from __future__ import annotations

import ipaddress
import socket


def get_local_ipv4s() -> list[str]:
    ips: set[str] = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass

    # UDP connect trick to find the primary LAN IP without sending packets.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass

    return sorted(ip for ip in ips if not ip.startswith("127."))


def primary_local_ip() -> str:
    ips = get_local_ipv4s()
    return ips[0] if ips else "127.0.0.1"


def same_lan_prefix(peer_ip: str, prefix_bits: int = 24) -> bool:
    try:
        peer = ipaddress.ip_address(peer_ip)
        if peer.is_loopback or peer.version != 4:
            return False
        for local in get_local_ipv4s():
            net = ipaddress.ip_network(f"{local}/{prefix_bits}", strict=False)
            if peer in net:
                return True
    except ValueError:
        return False
    return False


def allow_peer(peer_ip: str, securemode: bool) -> bool:
    if not securemode:
        return True
    return same_lan_prefix(peer_ip)
