from __future__ import annotations

import fnmatch
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Iterable


def cit_root() -> Path:
    return Path.home() / ".cit"


def workspace_root() -> Path:
    return cit_root() / "projects"


def exec_local_root() -> Path:
    return cit_root() / "exec_local"


def working_root() -> Path:
    return cit_root() / "working"


def backup_root() -> Path:
    return cit_root() / "backups"


def line_work_root() -> Path:
    return cit_root() / "tmp" / "lns"


def ensure_workspace() -> Path:
    for root in (workspace_root(), exec_local_root(), working_root(), backup_root(), line_work_root()):
        root.mkdir(parents=True, exist_ok=True)
    return workspace_root()


def sanitize_project_name(name: str) -> str:
    cleaned = "".join(c for c in name.strip() if c.isalnum() or c in ("-", "_", " ")).strip()
    if not cleaned:
        raise ValueError("Projektname ist leer oder ungueltig.")
    return cleaned[:80]


def project_path(project_name: str) -> Path:
    return ensure_workspace() / sanitize_project_name(project_name)


def _new_project_id() -> str:
    return "cit-" + uuid.uuid4().hex


def project_id_path(project_root: Path) -> Path:
    return project_root / "cit_id.txt"


def ensure_project_id(project_root: Path) -> str:
    project_root.mkdir(parents=True, exist_ok=True)
    p = project_id_path(project_root)
    if p.exists():
        for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            text = raw.strip()
            if text and not text.startswith("#"):
                return text
    pid = _new_project_id()
    p.write_text(pid + "\n# Nicht löschen: Cit braucht diese Projekt-ID, um spätere Verbindungen, Working-Kopien und Syncs demselben Projekt zuzuordnen.\n", encoding="utf-8")
    return pid


def read_project_id(project_root: Path) -> str:
    return ensure_project_id(project_root)


def config_path(project_root: Path) -> Path:
    return project_root / ".cit_config.json"


def load_config(project_root: Path) -> dict:
    p = config_path(project_root)
    if not p.exists():
        return {"start_file": "", "run_args": "", "python": "python"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("start_file", "")
            data.setdefault("run_args", "")
            data.setdefault("python", "python")
            return data
    except Exception:
        pass
    return {"start_file": "", "run_args": "", "python": "python"}


def save_config(project_root: Path, config: dict) -> None:
    config_path(project_root).write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def create_default_ignore(project_root: Path) -> None:
    p = project_root / "cit_ignore.txt"
    if not p.exists():
        p.write_text("""# Cit ignore file\n__pycache__/\n*.pyc\n.venv/\nvenv/\n.env/\n.git/\ndist/\nbuild/\n*.log\n""", encoding="utf-8")


def create_default_denyai(project_root: Path) -> None:
    """Create the per-project AI deny list template if it does not exist."""
    p = project_root / "denyai.txt"
    if not p.exists():
        p.write_text(
            """# DenyAI file for Cit\n"""
            """# Add files or folders here that the OpenAI bot must not read, edit, delete, move or overwrite.\n"""
            """# One rule per line. Paths are relative to the project root.\n"""
            """# Examples:\n"""
            """# .env\n"""
            """# secrets.txt\n"""
            """# private/\n"""
            """# *.key\n"""
            """\n""",
            encoding="utf-8",
        )


def create_project(project_name: str, project_id: str | None = None) -> Path:
    root = project_path(project_name)
    root.mkdir(parents=True, exist_ok=True)
    id_file = project_id_path(root)
    if project_id and not id_file.exists():
        id_file.write_text(project_id.strip() + "\n# Nicht löschen: Cit braucht diese Projekt-ID, um spätere Verbindungen, Working-Kopien und Syncs demselben Projekt zuzuordnen.\n", encoding="utf-8")
    ensure_project_id(root)
    create_default_ignore(root)
    create_default_denyai(root)
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(f"# {project_name}\n\nCit-Projekt.\n", encoding="utf-8")
    return root


def list_projects() -> list[str]:
    root = ensure_workspace()
    projects = []
    for p in root.iterdir():
        if p.is_dir():
            ensure_project_id(p)
            create_default_ignore(p)
            create_default_denyai(p)
            projects.append(p.name)
    return sorted(projects)


def projects_info() -> list[dict[str, str]]:
    out = []
    for name in list_projects():
        root = project_path(name)
        out.append({"name": name, "id": read_project_id(root)})
    return out


def find_project_by_id(project_id: str) -> str | None:
    if not project_id:
        return None
    for name in list_projects():
        if read_project_id(project_path(name)) == project_id:
            return name
    return None


def choose_local_project_name(remote_name: str, project_id: str | None) -> str:
    if project_id:
        existing = find_project_by_id(project_id)
        if existing:
            return existing
    base = sanitize_project_name(remote_name)
    candidate = base
    i = 2
    while project_path(candidate).exists():
        try:
            if project_id and read_project_id(project_path(candidate)) == project_id:
                return candidate
        except Exception:
            pass
        candidate = f"{base}-{i}"
        i += 1
    return candidate


def safe_project_path(project_root: Path, requested_path: str) -> Path:
    if requested_path is None:
        raise PermissionError("Leerer Pfad blockiert.")
    requested_path = str(requested_path).strip().replace("\\", "/")
    if not requested_path:
        raise PermissionError("Leerer Pfad blockiert.")
    raw = Path(requested_path)
    if raw.is_absolute():
        raise PermissionError("Absolute Pfade sind verboten.")
    project_root = project_root.resolve()
    target = (project_root / raw).resolve()
    try:
        target.relative_to(project_root)
    except ValueError as exc:
        raise PermissionError("Zugriff ausserhalb des Projektordners blockiert.") from exc
    return target


def rel_to_project(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def read_ignore_patterns(project_root: Path) -> list[str]:
    p = project_root / "cit_ignore.txt"
    patterns = ["__pycache__/", ".git/", ".citstate/", ".cit_lines/", "*.pyc", "*.pyo"]
    if p.exists():
        for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line.replace("\\", "/"))
    return patterns


def ignored_by_patterns(rel: str, patterns: list[str]) -> bool:
    rel = rel.replace("\\", "/")
    parts = rel.split("/")
    for pat in patterns:
        p = pat.strip().replace("\\", "/")
        if not p:
            continue
        if p.endswith("/"):
            name = p[:-1]
            if name in parts or rel.startswith(p):
                return True
        if fnmatch.fnmatch(rel, p) or any(fnmatch.fnmatch(part, p) for part in parts):
            return True
    return False


def iter_project_files(project_root: Path) -> Iterable[Path]:
    project_root = project_root.resolve()
    patterns = read_ignore_patterns(project_root)
    for root, dirs, files in os.walk(project_root):
        current = Path(root).resolve()
        safe_dirs = []
        for d in dirs:
            candidate = (current / d).resolve()
            try:
                rel = candidate.relative_to(project_root).as_posix() + "/"
            except ValueError:
                continue
            if ignored_by_patterns(rel, patterns):
                continue
            safe_dirs.append(d)
        dirs[:] = safe_dirs
        for filename in files:
            p = (current / filename).resolve()
            try:
                rel = p.relative_to(project_root).as_posix()
            except ValueError:
                continue
            if ignored_by_patterns(rel, patterns):
                continue
            if p.is_file():
                yield p


def create_file(project_root: Path, rel_path: str, content: str = "") -> Path:
    target = safe_project_path(project_root, rel_path)
    if target.exists():
        raise FileExistsError("Diese Datei existiert schon.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def create_folder(project_root: Path, rel_path: str) -> Path:
    target = safe_project_path(project_root, rel_path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def rename_path(project_root: Path, rel_path: str, new_name: str) -> str:
    if not new_name or any(c in new_name for c in "\\/:"):
        raise ValueError("Ungueltiger neuer Name.")
    src = safe_project_path(project_root, rel_path)
    if not src.exists():
        raise FileNotFoundError(rel_path)
    parent_rel = src.parent.relative_to(project_root.resolve()).as_posix()
    dst_rel = f"{parent_rel}/{new_name}" if parent_rel != "." else new_name
    dst = safe_project_path(project_root, dst_rel)
    if dst.exists():
        raise FileExistsError("Ziel existiert schon.")
    src.rename(dst)
    return rel_to_project(project_root, dst)


def move_path(project_root: Path, rel_path: str, new_rel_path: str) -> str:
    src = safe_project_path(project_root, rel_path)
    dst = safe_project_path(project_root, new_rel_path)
    if not src.exists():
        raise FileNotFoundError(rel_path)
    if dst.exists():
        raise FileExistsError("Ziel existiert schon.")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return rel_to_project(project_root, dst)


def delete_path(project_root: Path, rel_path: str) -> None:
    target = safe_project_path(project_root, rel_path)
    if not target.exists():
        return
    if target == project_root.resolve():
        raise PermissionError("Der Projektordner selbst darf nicht geloescht werden.")
    if target.name == "cit_id.txt":
        raise PermissionError("Cit-Systemdatei ist geschuetzt.")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def copy_project_tree(src_root: Path, dst_root: Path) -> None:
    src_root = src_root.resolve()
    if not src_root.exists():
        raise FileNotFoundError(src_root)
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.parent.mkdir(parents=True, exist_ok=True)
    patterns = read_ignore_patterns(src_root)
    def ignore(dir_path: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        base = Path(dir_path)
        for name in names:
            p = base / name
            try:
                rel = p.resolve().relative_to(src_root).as_posix()
                if p.is_dir():
                    rel += "/"
                if ignored_by_patterns(rel, patterns):
                    ignored.add(name)
            except Exception:
                pass
        return ignored
    shutil.copytree(src_root, dst_root, ignore=ignore)


def update_exec_local(project_root: Path) -> Path:
    ensure_workspace()
    target = exec_local_root() / read_project_id(project_root)
    copy_project_tree(project_root, target)
    return target


def save_working_copy(project_root: Path) -> Path:
    ensure_workspace()
    target = working_root() / read_project_id(project_root)
    copy_project_tree(project_root, target)
    return target


def create_backup(project_root: Path, label: str = "sync") -> Path:
    ensure_workspace()
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_label = "".join(c for c in label if c.isalnum() or c in ("-", "_"))[:32] or "backup"
    target = backup_root() / read_project_id(project_root) / f"{ts}_{safe_label}"
    copy_project_tree(project_root, target)
    return target


def restore_backup(project_root: Path, backup_path: Path) -> None:
    backup_path = backup_path.resolve()
    allowed = (backup_root() / read_project_id(project_root)).resolve()
    try:
        backup_path.relative_to(allowed)
    except ValueError as exc:
        raise PermissionError("Backup liegt nicht im Backup-Ordner dieses Projekts.") from exc
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    pid = read_project_id(project_root)
    if project_root.exists():
        shutil.rmtree(project_root)
    shutil.copytree(backup_path, project_root)
    ensure_project_id(project_root)
    (project_root / "cit_id.txt").write_text(pid + "\n", encoding="utf-8")


def list_backups(project_root: Path) -> list[Path]:
    root = backup_root() / read_project_id(project_root)
    if not root.exists():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir()], reverse=True)

# ---- Cit v2.0 sync safety snapshots (single rotating pre-sync backup + undo/redo) ----
def sync_snapshot_root() -> Path:
    return cit_root() / "sync_snapshots"


def _snapshot_path(project_root: Path, slot: str) -> Path:
    safe_slot = "".join(c for c in slot if c.isalnum() or c in ("-", "_")) or "snapshot"
    return sync_snapshot_root() / read_project_id(project_root) / safe_slot


def create_sync_snapshot(project_root: Path, slot: str = "latest_before_sync") -> Path:
    """Create one rotating project snapshot for sync undo/redo.

    Unlike manual backups this slot is overwritten each time, so automatic sync
    does not fill the disk with unlimited backup folders.
    """
    ensure_workspace()
    root = sync_snapshot_root()
    root.mkdir(parents=True, exist_ok=True)
    target = _snapshot_path(project_root, slot)
    copy_project_tree(project_root, target)
    return target


def snapshot_exists(project_root: Path, slot: str) -> bool:
    return _snapshot_path(project_root, slot).exists()


def restore_sync_snapshot(project_root: Path, slot: str) -> None:
    src = _snapshot_path(project_root, slot).resolve()
    allowed = (sync_snapshot_root() / read_project_id(project_root)).resolve()
    try:
        src.relative_to(allowed)
    except ValueError as exc:
        raise PermissionError("Snapshot liegt nicht im Sync-Snapshot-Ordner dieses Projekts.") from exc
    if not src.exists():
        raise FileNotFoundError(src)
    pid = read_project_id(project_root)
    if project_root.exists():
        shutil.rmtree(project_root)
    shutil.copytree(src, project_root)
    ensure_project_id(project_root)
    (project_root / "cit_id.txt").write_text(pid + "\n# Nicht löschen: Cit braucht diese Projekt-ID, um spätere Verbindungen, Working-Kopien und Syncs demselben Projekt zuzuordnen.\n", encoding="utf-8")
