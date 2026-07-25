from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from .workspace import cit_root, copy_project_tree, iter_project_files, read_project_id, safe_project_path, rel_to_project


def history_root(project_root: Path) -> Path:
    root = cit_root() / "history" / read_project_id(project_root)
    (root / "commits").mkdir(parents=True, exist_ok=True)
    return root


def _state_path(project_root: Path) -> Path:
    return history_root(project_root) / "state.json"


def _load_state(project_root: Path) -> dict:
    p = _state_path(project_root)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("current_branch", "main")
                data.setdefault("branches", {"main": None})
                return data
        except Exception:
            pass
    return {"current_branch": "main", "branches": {"main": None}}


def _save_state(project_root: Path, state: dict) -> None:
    p = _state_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def current_branch(project_root: Path) -> str:
    return str(_load_state(project_root).get("current_branch") or "main")


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_manifest(project_root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for p in iter_project_files(project_root):
        rel = rel_to_project(project_root, p)
        if rel.replace("\\", "/") == "cit_id.txt":
            continue
        manifest[rel] = _file_hash(p)
    return dict(sorted(manifest.items()))


def _commit_dir(project_root: Path, commit_id: str) -> Path:
    return history_root(project_root) / "commits" / commit_id


def _commit_meta_path(project_root: Path, commit_id: str) -> Path:
    return _commit_dir(project_root, commit_id) / "meta.json"


def get_head(project_root: Path, branch: str | None = None) -> str | None:
    state = _load_state(project_root)
    branch = branch or state.get("current_branch") or "main"
    return state.get("branches", {}).get(branch)


def create_commit(project_root: Path, message: str) -> dict:
    state = _load_state(project_root)
    branch = state.get("current_branch") or "main"
    message = (message or "Cit backup").strip()[:240]
    manifest = tree_manifest(project_root)
    digest = hashlib.sha1(json.dumps(manifest, sort_keys=True).encode("utf-8") + message.encode("utf-8")).hexdigest()[:8]
    ts = time.strftime("%Y%m%d_%H%M%S")
    commit_id = f"{ts}_{digest}"
    cdir = _commit_dir(project_root, commit_id)
    tree_dir = cdir / "tree"
    copy_project_tree(project_root, tree_dir)
    meta = {
        "id": commit_id,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "branch": branch,
        "parent": state.get("branches", {}).get(branch),
        "manifest": manifest,
    }
    cdir.mkdir(parents=True, exist_ok=True)
    _commit_meta_path(project_root, commit_id).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    state.setdefault("branches", {})[branch] = commit_id
    state["current_branch"] = branch
    _save_state(project_root, state)
    return meta


def list_commits(project_root: Path, limit: int = 80) -> list[dict]:
    commits = []
    commits_root = history_root(project_root) / "commits"
    for p in sorted(commits_root.iterdir(), reverse=True):
        if not p.is_dir():
            continue
        meta_path = p / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            commits.append(meta)
        except Exception:
            continue
        if len(commits) >= limit:
            break
    return commits


def commit_meta(project_root: Path, commit_id: str) -> dict:
    p = _commit_meta_path(project_root, commit_id)
    if not p.exists():
        raise FileNotFoundError(f"Commit nicht gefunden: {commit_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def status(project_root: Path) -> dict:
    head = get_head(project_root)
    current = tree_manifest(project_root)
    if not head:
        return {"head": None, "added": sorted(current), "modified": [], "deleted": [], "clean": False}
    meta = commit_meta(project_root, head)
    old = meta.get("manifest", {})
    added = sorted(set(current) - set(old))
    deleted = sorted(set(old) - set(current))
    modified = sorted(k for k in set(current) & set(old) if current[k] != old[k])
    return {"head": head, "added": added, "modified": modified, "deleted": deleted, "clean": not (added or modified or deleted)}


def diff_summary(project_root: Path, commit_id: str | None = None) -> list[str]:
    st = status(project_root) if commit_id is None else _diff_against(project_root, commit_id)
    lines = []
    for rel in st.get("added", []):
        lines.append(f"A  {rel}")
    for rel in st.get("modified", []):
        lines.append(f"M  {rel}")
    for rel in st.get("deleted", []):
        lines.append(f"D  {rel}")
    return lines or ["Keine Unterschiede."]


def _diff_against(project_root: Path, commit_id: str) -> dict:
    current = tree_manifest(project_root)
    old = commit_meta(project_root, commit_id).get("manifest", {})
    added = sorted(set(current) - set(old))
    deleted = sorted(set(old) - set(current))
    modified = sorted(k for k in set(current) & set(old) if current[k] != old[k])
    return {"head": commit_id, "added": added, "modified": modified, "deleted": deleted, "clean": not (added or modified or deleted)}


def branches(project_root: Path) -> tuple[str, dict]:
    state = _load_state(project_root)
    return state.get("current_branch", "main"), dict(state.get("branches", {"main": None}))


def create_branch(project_root: Path, name: str) -> None:
    name = (name or "").strip()
    if not name or any(c in name for c in "\\/:*?\"<>|") or ".." in name:
        raise ValueError("Ungueltiger Branch-Name.")
    state = _load_state(project_root)
    state.setdefault("branches", {})[name] = state.get("branches", {}).get(state.get("current_branch", "main"))
    _save_state(project_root, state)


def checkout_branch(project_root: Path, name: str) -> None:
    state = _load_state(project_root)
    if name not in state.get("branches", {}):
        raise FileNotFoundError(f"Branch nicht gefunden: {name}")
    commit_id = state["branches"].get(name)
    if commit_id:
        restore_commit(project_root, commit_id)
    state = _load_state(project_root)
    state["current_branch"] = name
    _save_state(project_root, state)


def restore_commit(project_root: Path, commit_id: str) -> None:
    cdir = _commit_dir(project_root, commit_id) / "tree"
    if not cdir.exists():
        raise FileNotFoundError(f"Commit-Daten fehlen: {commit_id}")
    pid_text = (project_root / "cit_id.txt").read_text(encoding="utf-8", errors="ignore") if (project_root / "cit_id.txt").exists() else ""
    for child in list(project_root.iterdir()):
        if child.name == "cit_id.txt":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in cdir.iterdir():
        if child.name == "cit_id.txt":
            continue
        dst = project_root / child.name
        if child.is_dir():
            shutil.copytree(child, dst)
        else:
            shutil.copy2(child, dst)
    if pid_text:
        (project_root / "cit_id.txt").write_text(pid_text, encoding="utf-8")


def merge_branch(project_root: Path, branch_name: str) -> list[str]:
    current, brs = branches(project_root)
    if branch_name not in brs:
        raise FileNotFoundError(f"Branch nicht gefunden: {branch_name}")
    commit_id = brs.get(branch_name)
    if not commit_id:
        return [f"Branch {branch_name} hat noch keinen Backup/Commit."]
    src_tree = _commit_dir(project_root, commit_id) / "tree"
    if not src_tree.exists():
        raise FileNotFoundError(f"Commit-Daten fehlen: {commit_id}")
    changed = []
    conflicts = []
    for src in src_tree.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(src_tree).as_posix()
        if rel == "cit_id.txt":
            continue
        dst = safe_project_path(project_root, rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and _file_hash(dst) != _file_hash(src):
            conflict = dst.with_name(dst.stem + f"_MERGE_{branch_name}" + dst.suffix)
            shutil.copy2(src, conflict)
            conflicts.append(rel)
        elif not dst.exists():
            shutil.copy2(src, dst)
            changed.append(rel)
    out = []
    if changed:
        out.append("Gemergte neue Dateien: " + ", ".join(changed[:20]))
    if conflicts:
        out.append("Konflikte als *_MERGE_<branch> gesichert: " + ", ".join(conflicts[:20]))
    return out or ["Merge abgeschlossen, keine neuen Unterschiede."]


def delete_branch(project_root: Path, name: str) -> None:
    name = (name or '').strip()
    if name == 'main':
        raise ValueError('main kann nicht geloescht werden.')
    state = _load_state(project_root)
    if name not in state.get('branches', {}):
        raise FileNotFoundError(f'Branch nicht gefunden: {name}')
    del state.setdefault('branches', {})[name]
    if state.get('current_branch') == name:
        state['current_branch'] = 'main'
    _save_state(project_root, state)


def promote_branch_to_main(project_root: Path, branch_name: str) -> list[str]:
    branch_name = (branch_name or '').strip()
    state = _load_state(project_root)
    brs = state.setdefault('branches', {'main': None})
    if branch_name == 'main':
        return ['Branch main ist bereits die Main-Version.']
    if branch_name not in brs:
        raise FileNotFoundError(f'Branch nicht gefunden: {branch_name}')
    commit_id = brs.get(branch_name)
    if not commit_id:
        raise ValueError(f'Branch {branch_name} hat noch keinen Backup/Commit.')
    # Safety-Commit vom aktuellen Stand, bevor main ueberschrieben wird.
    old_current = state.get('current_branch', 'main')
    state['current_branch'] = 'main'
    _save_state(project_root, state)
    try:
        create_commit(project_root, f'Auto-Safety: main vor Uebernahme von {branch_name}')
    except Exception:
        pass
    restore_commit(project_root, commit_id)
    state = _load_state(project_root)
    state.setdefault('branches', {})['main'] = commit_id
    if branch_name in state['branches']:
        del state['branches'][branch_name]
    state['current_branch'] = 'main'
    _save_state(project_root, state)
    return [
        f'Branch {branch_name} wurde als neue main-Version uebernommen.',
        f'Der Branch-Eintrag {branch_name} wurde entfernt. Die Dateien bleiben als main erhalten.',
        'Vorher wurde ein Safety-Backup fuer main versucht.'
    ]
