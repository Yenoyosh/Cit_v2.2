from __future__ import annotations

import socket
import threading
from pathlib import Path
from typing import Callable, Optional

from . import sync
from .protocol import b64, recv_msg, send_msg, unb64
from .security import allow_peer
from .workspace import (
    create_backup, create_file, create_folder, create_project, delete_path,
    move_path, project_path, read_project_id, rename_path, choose_local_project_name
)
from .line_split import split_file_into_lines, merge_lines_back
from .terminal_security import terminal_block_reason

CONTROL_PORT = 50110

PERM_READ = "read_only"
PERM_WRITE = "read_write"
PERM_FULL = "full"

class CitConnection:
    def __init__(self, sock: socket.socket, peer_ip: str, project_root: Path, name: str, on_event: Callable[[str, object], None], permissions: str = PERM_FULL):
        self.sock = sock
        self.peer_ip = peer_ip
        self.project_root = project_root
        self.name = name
        self.on_event = on_event
        self.permissions = permissions
        self.lock = threading.Lock()
        self.running = True
        self.last_seen: dict[str, str] = {}
        self.remote_locks: dict[str, str] = {}
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def can_write(self) -> bool:
        return self.permissions in (PERM_WRITE, PERM_FULL)

    def can_full(self) -> bool:
        return self.permissions == PERM_FULL

    def close(self) -> None:
        self.running = False
        try:
            self.send({"type": "bye"})
        except Exception:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, msg: dict) -> None:
        with self.lock:
            send_msg(self.sock, msg)

    def chat(self, text: str) -> None:
        self.send({"type": "chat", "text": text})

    def request_sync(self) -> None:
        self.send({"type": "manifest", "files": sync.manifest(self.project_root)})

    def send_file(self, rel: str) -> None:
        data = sync.read_file_payload(self.project_root, rel)
        self.send({"type": "file", "path": rel, "data": b64(data), "sha256": sync.sha256_bytes(data)})

    def file_op(self, op: str, path: str, target: str = "", is_folder: bool = False) -> None:
        self.send({"type": "file_op", "op": op, "path": path, "target": target, "is_folder": is_folder})

    def lock_file(self, path: str, locked: bool = True) -> None:
        self.send({"type": "lock", "path": path, "locked": locked})

    def line_split_request(self, path: str) -> None:
        self.send({"type": "line_split", "path": path})

    def line_merge_request(self, path: str) -> None:
        self.send({"type": "line_merge", "path": path})

    def whiteboard(self, data: bytes) -> None:
        self.send({"type": "whiteboard", "data": b64(data)})

    def camera_request(self) -> None:
        self.send({"type": "camera_request"})

    def camera_frame(self, data: bytes) -> None:
        self.send({"type": "camera_frame", "data": b64(data)})

    def camera_stop(self) -> None:
        self.send({"type": "camera_stop"})

    def remote_terminal_command(self, command: str, cwd_rel: str = "") -> None:
        reason = terminal_block_reason(command)
        if reason:
            raise PermissionError(reason)
        self.send({"type": "remote_terminal_request", "command": command, "cwd_rel": cwd_rel})

    def remote_terminal_output(self, text: str) -> None:
        self.send({"type": "remote_terminal_output", "text": text})

    def remote_terminal_status(self, text: str) -> None:
        self.send({"type": "remote_terminal_status", "text": text})

    def _require_write(self) -> None:
        if not self.can_write():
            raise PermissionError("Gegenstelle hat nur Leserechte.")

    def _require_full(self) -> None:
        if not self.can_full():
            raise PermissionError("Gegenstelle hat keine Vollrechte fuer diese Aktion.")

    def _apply_file_op(self, msg: dict) -> None:
        op = str(msg.get("op", ""))
        path = str(msg.get("path", ""))
        target = str(msg.get("target", ""))
        is_folder = bool(msg.get("is_folder", False))
        if op in {"create", "rename", "move"}:
            self._require_write()
        if op == "delete":
            self._require_full()
        create_backup(self.project_root, "before_file_op")
        if op == "create":
            if is_folder:
                create_folder(self.project_root, path)
            else:
                create_file(self.project_root, path, "")
        elif op == "rename":
            rename_path(self.project_root, path, target)
        elif op == "move":
            move_path(self.project_root, path, target)
        elif op == "delete":
            delete_path(self.project_root, path)
        else:
            raise ValueError("Unbekannte Dateioperation.")
        self.on_event("file_tree_changed", f"Remote-Dateioperation: {op} {path}")

    def _reader(self) -> None:
        while self.running:
            try:
                msg = recv_msg(self.sock)
                typ = msg.get("type")
                if typ == "chat":
                    self.on_event("chat", f"{self.peer_ip}: {msg.get('text','')}")
                elif typ == "manifest":
                    remote = msg.get("files", {})
                    local = sync.manifest(self.project_root)
                    plan = sync.build_sync_plan(local, remote, self.last_seen)
                    if plan.conflicts:
                        self.on_event("conflict", plan.conflicts)
                    for rel in plan.need_from_peer:
                        self.send({"type": "get_file", "path": rel})
                    for rel in plan.send_to_peer:
                        try:
                            self.send_file(rel)
                        except Exception as e:
                            self.on_event("status", f"Konnte {rel} nicht senden: {e}")
                    both = sync.manifest(self.project_root)
                    for p, meta in both.items():
                        self.last_seen[p] = meta["sha256"]
                    self.on_event("status", f"Sync fertig: {len(plan.need_from_peer)} empfangen, {len(plan.send_to_peer)} gesendet, {len(plan.conflicts)} Konflikte.")
                elif typ == "get_file":
                    self.send_file(str(msg.get("path", "")))
                elif typ == "file":
                    self._require_write()
                    rel = str(msg.get("path", ""))
                    data = unb64(str(msg.get("data", "")))
                    expected_hash = str(msg.get("sha256", ""))
                    if expected_hash and sync.sha256_bytes(data) != expected_hash:
                        raise ValueError(f"Hashprüfung fehlgeschlagen für {rel}")
                    # Cit v2.2: Offline-Konflikte werden nicht mehr mit Merge-Popup
                    # behandelt. Eingehende Datei ueberschreibt lokal, Backup davor.
                    sync.write_file_payload(self.project_root, rel, data, backup=False)
                    h = sync.manifest(self.project_root).get(rel, {}).get("sha256")
                    if h:
                        self.last_seen[rel] = h
                    self.on_event("file_tree_changed", f"Datei empfangen/ueberschrieben: {rel}")
                elif typ == "file_op":
                    self._apply_file_op(msg)
                elif typ == "lock":
                    path = str(msg.get("path", ""))
                    locked = bool(msg.get("locked", False))
                    if locked:
                        self.remote_locks[path] = self.peer_ip
                    else:
                        self.remote_locks.pop(path, None)
                    self.on_event("lock_update", dict(self.remote_locks))
                elif typ == "line_split":
                    self._require_write()
                    path = str(msg.get("path", ""))
                    split_file_into_lines(self.project_root, path)
                    self.on_event("file_tree_changed", f"Line-Split remote erstellt fuer: {path}")
                elif typ == "line_merge":
                    self._require_write()
                    path = str(msg.get("path", ""))
                    merge_lines_back(self.project_root, path)
                    self.on_event("file_tree_changed", f"Line-Split remote zusammengefuegt fuer: {path}")
                elif typ == "whiteboard":
                    self.on_event("whiteboard", str(msg.get("data", "")))
                elif typ == "camera_request":
                    self.on_event("camera_request", {"peer_ip": self.peer_ip, "connection": self})
                elif typ == "camera_frame":
                    self.on_event("camera_frame", {"peer_ip": self.peer_ip, "data": str(msg.get("data", ""))})
                elif typ == "camera_stop":
                    self.on_event("camera_stop", self.peer_ip)
                elif typ == "remote_terminal_request":
                    command = str(msg.get("command", ""))
                    reason = terminal_block_reason(command)
                    if reason:
                        self.remote_terminal_status(reason)
                    else:
                        self.on_event("remote_terminal_request", {"command": command, "cwd_rel": str(msg.get("cwd_rel", "")), "peer_ip": self.peer_ip, "connection": self})
                elif typ == "remote_terminal_output":
                    self.on_event("remote_terminal_output", f"[{self.peer_ip}] " + str(msg.get("text", "")))
                elif typ == "remote_terminal_status":
                    self.on_event("remote_terminal_status", f"[{self.peer_ip}] " + str(msg.get("text", "")))
                elif typ == "sync_now":
                    self.request_sync()
                elif typ == "ping":
                    self.on_event("status", f"Ping von {self.peer_ip} empfangen.")
                    self.send({"type":"pong", "time": msg.get("time")})
                elif typ == "pong":
                    self.on_event("status", f"Pong von {self.peer_ip} empfangen.")
                elif typ == "bye":
                    self.on_event("status", "Gegenstelle hat die Zusammenarbeit beendet.")
                    self.close()
                    break
            except socket.timeout:
                # Should not normally happen because Cit uses blocking sockets,
                # but do not kill the whole app or pretend the peer is gone.
                self.on_event("status", "Netzwerk wartete zu lange auf Daten; Verbindung bleibt aktiv.")
                continue
            except Exception as e:
                self.on_event("status", f"Verbindung beendet: {e}")
                self.close()
                break

class CitServer:
    def __init__(self, securemode_getter: Callable[[], bool], on_request: Callable[[str, str], str | bool], on_connected: Callable[[CitConnection], None], on_event: Callable[[str, object], None]):
        self.securemode_getter = securemode_getter
        self.on_request = on_request
        self.on_connected = on_connected
        self.on_event = on_event
        self.stop = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", CONTROL_PORT))
        srv.listen(12)
        srv.settimeout(0.5)
        self.on_event("status", f"Host bereit auf TCP {CONTROL_PORT}.")
        while not self.stop.is_set():
            try:
                client, addr = srv.accept()
                # Accepted sockets must stay blocking. A timeout on the control
                # socket makes an idle, healthy connection look like a broken
                # one and causes random "timed out" disconnects.
                try:
                    client.settimeout(None)
                except OSError:
                    pass
                threading.Thread(target=self._handle_client, args=(client, addr[0]), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break
        srv.close()

    def _handle_client(self, sock: socket.socket, ip: str) -> None:
        try:
            if not allow_peer(ip, self.securemode_getter()):
                send_msg(sock, {"type": "reject", "reason": "Securemode blockiert diese IP."})
                sock.close(); return
            hello = recv_msg(sock)
            if hello.get("type") != "connect_request":
                sock.close(); return
            project = str(hello.get("project", ""))
            decision = self.on_request(ip, project)
            if not decision:
                send_msg(sock, {"type": "reject", "reason": "Host hat abgelehnt."})
                sock.close(); return
            permissions = decision if isinstance(decision, str) else PERM_FULL
            root = project_path(project)
            project_id = read_project_id(root)
            send_msg(sock, {"type": "accept", "project": project, "project_id": project_id, "permissions": permissions})
            conn = CitConnection(sock, ip, root, "host", self.on_event, permissions=permissions)
            self.on_connected(conn)
        except Exception as e:
            self.on_event("status", f"Clientfehler {ip}: {e}")
            try:
                sock.close()
            except OSError:
                pass

def connect_to(ip: str, project: str, on_event: Callable[[str, object], None], project_id: str = "", mode: str = "live") -> CitConnection:
    local_name = choose_local_project_name(project, project_id)
    root = create_project(local_name, project_id if project_id else None)
    sock = socket.create_connection((ip, CONTROL_PORT), timeout=8)
    # create_connection leaves the timeout on the socket. After the connection
    # handshake Cit uses a persistent idle TCP stream, so it must be blocking;
    # otherwise recv_msg raises socket.timeout after a few quiet seconds.
    sock.settimeout(None)
    send_msg(sock, {"type": "connect_request", "project": project, "project_id": read_project_id(root), "mode": mode})
    answer = recv_msg(sock)
    if answer.get("type") != "accept":
        raise ConnectionError(answer.get("reason", "Verbindung abgelehnt."))
    remote_id = str(answer.get("project_id", project_id or ""))
    if remote_id:
        id_file = root / "cit_id.txt"
        current_id = id_file.read_text(encoding="utf-8", errors="ignore").strip() if id_file.exists() else ""
        if not current_id or not project_id:
            id_file.write_text(remote_id + "\n", encoding="utf-8")
    permissions = str(answer.get("permissions", PERM_FULL))
    on_event("status", f"Host hat Rechte gesetzt: {permissions}")
    return CitConnection(sock, ip, root, "client", on_event, permissions=PERM_FULL)
