from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import iter_project_files, rel_to_project, safe_project_path, read_ignore_patterns, ignored_by_patterns, create_backup

MAX_FILE_SIZE = 8 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_ignore(project_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return True
    if path.is_dir():
        rel += "/"
    return ignored_by_patterns(rel, read_ignore_patterns(project_root))


def manifest(project_root: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in iter_project_files(project_root):
        try:
            size = p.stat().st_size
            if size > MAX_FILE_SIZE:
                continue
            rel = rel_to_project(project_root, p)
            out[rel] = {"sha256": sha256_file(p), "size": size, "mtime": p.stat().st_mtime}
        except OSError:
            continue
    return out


def read_file_payload(project_root: Path, rel_path: str) -> bytes:
    target = safe_project_path(project_root, rel_path)
    if should_ignore(project_root, target):
        raise PermissionError("Ignorierter Pfad blockiert.")
    if not target.is_file():
        raise FileNotFoundError(rel_path)
    if target.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("Datei zu gross fuer Cit.")
    return target.read_bytes()


def write_file_payload(project_root: Path, rel_path: str, data: bytes, backup: bool = True) -> None:
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("Datei zu gross fuer Cit.")
    target = safe_project_path(project_root, rel_path)
    if should_ignore(project_root, target):
        raise PermissionError("Ignorierter Pfad blockiert.")
    if backup and target.exists():
        create_backup(project_root, "before_remote_write")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def create_conflict_copy(project_root: Path, rel_path: str, data: bytes, suffix: str = "remote_conflict") -> str:
    target = safe_project_path(project_root, rel_path)
    base = target.name
    new_name = f"{base}.{suffix}"
    rel_parent = target.parent.relative_to(project_root.resolve()).as_posix()
    conflict_rel = new_name if rel_parent == "." else f"{rel_parent}/{new_name}"
    conflict_path = safe_project_path(project_root, conflict_rel)
    i = 2
    while conflict_path.exists():
        new_name = f"{base}.{suffix}_{i}"
        conflict_rel = new_name if rel_parent == "." else f"{rel_parent}/{new_name}"
        conflict_path = safe_project_path(project_root, conflict_rel)
        i += 1
    conflict_path.write_bytes(data)
    return conflict_rel


@dataclass
class SyncPlan:
    need_from_peer: list[str]
    send_to_peer: list[str]
    conflicts: list[str]


def build_sync_plan(local: dict[str, dict[str, Any]], remote: dict[str, dict[str, Any]], last_seen: dict[str, str]) -> SyncPlan:
    need_from_peer: list[str] = []
    send_to_peer: list[str] = []
    conflicts: list[str] = []
    paths = set(local) | set(remote)
    for path in sorted(paths):
        l = local.get(path)
        r = remote.get(path)
        old = last_seen.get(path)
        lhash = l.get("sha256") if l else None
        rhash = r.get("sha256") if r else None
        if lhash == rhash:
            continue
        local_changed = lhash is not None and lhash != old
        remote_changed = rhash is not None and rhash != old
        if old is None:
            if l and r:
                if l.get("mtime", 0) >= r.get("mtime", 0):
                    send_to_peer.append(path)
                else:
                    need_from_peer.append(path)
            elif l:
                send_to_peer.append(path)
            elif r:
                need_from_peer.append(path)
        elif local_changed and remote_changed:
            # Cit v2.0: keine Merge-Frage bei Offline-Edits. Last-Write-Wins,
            # damit Sync wieder schlicht funktioniert. Gleichzeitig bearbeitete
            # Dateien werden ueber Fokus/Lock erkannt und per Line-Split behandelt.
            if (r or {}).get("mtime", 0) >= (l or {}).get("mtime", 0):
                need_from_peer.append(path)
            else:
                send_to_peer.append(path)
        elif remote_changed:
            need_from_peer.append(path)
        elif local_changed:
            send_to_peer.append(path)
    return SyncPlan(need_from_peer, send_to_peer, conflicts)
