from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

from .workspace import line_work_root, read_project_id, safe_project_path


def _safe_name(rel_path: str) -> str:
    return rel_path.replace("/", "__").replace("\\", "__").replace(":", "_")


def split_dir_for(project_root: Path, rel_path: str) -> Path:
    pid = read_project_id(project_root)
    return line_work_root() / pid / _safe_name(rel_path)


def _block_size(line_count: int) -> int:
    # Stufen, damit NTFS nicht unnötig viele Dateien bekommt.
    # <=100: 10er-Bloecke, <=1000: 100er, >=10k: 1000er.
    if line_count <= 100:
        return 10
    if line_count <= 1000:
        return 100
    return 1000


def _id_for(text: str, index: int) -> str:
    raw = f"{index}:{uuid.uuid4().hex}:{text}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:10]


def split_file_into_lines(project_root: Path, rel_path: str) -> Path:
    src = safe_project_path(project_root, rel_path)
    if not src.is_file():
        raise FileNotFoundError(rel_path)
    text = src.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    dst = split_dir_for(project_root, rel_path)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    block = _block_size(len(lines))
    meta = {
        "source": rel_path,
        "line_count": len(lines),
        "mode": "blocks",
        "block_size": block,
        "note": "Cit v2.0: temporärer Line-Split mit stabilen IDs. Wird nach Merge gelöscht.",
    }
    (dst / "_cit_lines_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if not lines:
        bid = _id_for("", 1)
        (dst / f"block_000001_{bid}.txt").write_text("", encoding="utf-8")
        return dst
    for start in range(0, len(lines), block):
        chunk = "".join(lines[start:start+block])
        num = start // block + 1
        bid = _id_for(chunk, num)
        (dst / f"block_{num:06d}_{bid}.txt").write_text(chunk, encoding="utf-8")
    return dst


def explode_block_to_lines(project_root: Path, rel_path: str, block_file_name: str) -> Path:
    """Optional next step: cut one contested block into individual line files."""
    folder = split_dir_for(project_root, rel_path)
    block_file = folder / block_file_name
    if not block_file.exists():
        raise FileNotFoundError(block_file_name)
    text = block_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    sub = folder / (block_file.stem + "__lines")
    if sub.exists():
        shutil.rmtree(sub)
    sub.mkdir(parents=True, exist_ok=True)
    for i, line in enumerate(lines, 1):
        lid = _id_for(line, i)
        (sub / f"line_{i:06d}_{lid}.txt").write_text(line, encoding="utf-8")
    block_file.unlink()
    return sub


def explode_line_to_chars(project_root: Path, rel_path: str, line_file: Path) -> Path:
    """Optional final step: cut one contested line into chars."""
    text = line_file.read_text(encoding="utf-8", errors="replace")
    sub = line_file.parent / (line_file.stem + "__chars")
    if sub.exists():
        shutil.rmtree(sub)
    sub.mkdir(parents=True, exist_ok=True)
    for i, ch in enumerate(text, 1):
        cid = _id_for(ch, i)
        (sub / f"char_{i:06d}_{cid}.txt").write_text(ch, encoding="utf-8")
    line_file.unlink()
    return sub


def _collect_text(folder: Path) -> str:
    out: list[str] = []
    for p in sorted(folder.iterdir()):
        if p.name.startswith("_"):
            continue
        if p.is_dir() and (p.name.endswith("__lines") or p.name.endswith("__chars")):
            out.append(_collect_text(p))
        elif p.is_file() and (p.name.startswith("block_") or p.name.startswith("line_") or p.name.startswith("char_")):
            out.append(p.read_text(encoding="utf-8", errors="replace"))
    return "".join(out)


def merge_lines_back(project_root: Path, line_dir_rel_or_file_rel: str) -> Path:
    candidate = split_dir_for(project_root, line_dir_rel_or_file_rel)
    meta_path = candidate / "_cit_lines_meta.json"
    if not meta_path.exists():
        # Allow direct tmp path only if it is inside Cit line temp root.
        raw = Path(line_dir_rel_or_file_rel)
        if raw.exists():
            candidate = raw
            meta_path = candidate / "_cit_lines_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError("Kein Cit-Line-Split-Metafile gefunden.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    source = str(meta.get("source", ""))
    target = safe_project_path(project_root, source)
    target.write_text(_collect_text(candidate), encoding="utf-8")
    shutil.rmtree(candidate, ignore_errors=True)
    return target
