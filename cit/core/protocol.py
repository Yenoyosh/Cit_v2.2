from __future__ import annotations

import base64
import json
import socket
import struct
from typing import Any

MAX_FRAME = 64 * 1024 * 1024


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def send_msg(sock: socket.socket, msg: dict[str, Any]) -> None:
    raw = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_FRAME:
        raise ValueError("Nachricht ist zu gross.")
    sock.sendall(struct.pack("!I", len(raw)) + raw)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("Verbindung geschlossen.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_msg(sock: socket.socket) -> dict[str, Any]:
    header = recv_exact(sock, 4)
    (size,) = struct.unpack("!I", header)
    if size <= 0 or size > MAX_FRAME:
        raise ValueError("Ungueltige Nachrichtengroesse.")
    raw = recv_exact(sock, size)
    msg = json.loads(raw.decode("utf-8"))
    if not isinstance(msg, dict):
        raise ValueError("Ungueltiges Nachrichtenformat.")
    return msg
