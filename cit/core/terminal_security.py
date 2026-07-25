from __future__ import annotations

import re
import shlex

# This is a safety guard for the integrated/remote terminal. It is intentionally
# conservative and blocks commands that can destroy disks, boot data, accounts,
# or large parts of the filesystem. It is not a replacement for OS permissions.
DANGEROUS_EXACT = {
    "diskpart", "format", "fdisk", "mkfs", "parted", "gparted", "dd",
    "shutdown", "reboot", "poweroff", "halt", "bcdedit", "bootrec", "bootsect",
    "reg", "regedit", "cipher", "takeown", "icacls", "net", "sc", "schtasks",
}

DANGEROUS_PATTERNS = [
    r"\bdiskpart\b",
    r"\bformat\b\s+[a-z]:",
    r"\bformat\b\s*/",
    r"\bclean\b\s*(?:all)?\b",
    r"\bselect\s+disk\b",
    r"\bdelete\s+partition\b",
    r"\bconvert\s+(?:gpt|mbr)\b",
    r"\bmkfs(?:\.[a-z0-9]+)?\b",
    r"\bdd\b.*\bof\s*=\s*/dev/",
    r"\brm\b\s+.*-(?:r|f|rf|fr)\b.*(?:/|\*)",
    r"\brmdir\b\s+.*\/(?:s|q)\b",
    r"\brd\b\s+.*\/(?:s|q)\b",
    r"\bdel\b\s+.*\/(?:s|q|f)\b.*(?:\*|[a-z]:\\)",
    r"\bremove-item\b.*-(?:recurse|force)\b",
    r"\berase\b\s+.*(?:\*|[a-z]:\\)",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bbcdedit\b",
    r"\bbootrec\b",
    r"\bbootsect\b",
    r"\breg\s+(?:delete|add|import)\b",
    r"\bregedit\b",
    r"\bcipher\b\s*/w",
    r"\btakeown\b\s+.*\/(?:f|r)\b",
    r"\bicacls\b\s+.*\/(?:grant|deny|remove|reset)\b",
    r"\bnet\s+user\b",
    r"\bnet\s+localgroup\b",
    r"\bsc\s+(?:delete|create|config|stop)\b",
    r"\bschtasks\b\s+.*/(?:create|delete|change)\b",
    r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*}\s*;\s*:",
]


def _tokens(command: str) -> list[str]:
    try:
        return [t.lower().strip() for t in shlex.split(command, posix=False)]
    except Exception:
        return [t.lower().strip() for t in re.split(r"\s+", command)]


def terminal_block_reason(command: str) -> str | None:
    raw = (command or "").strip()
    if not raw:
        return "Leerer Befehl."
    lowered = raw.lower()
    tokens = _tokens(raw)
    first = tokens[0].strip('"\'').lower() if tokens else ""
    first_base = first.replace(".exe", "").replace(".bat", "").replace(".cmd", "")
    if first_base in DANGEROUS_EXACT:
        return f"Blockiert: '{first_base}' ist fuer Cit-Terminal zu gefaehrlich."
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return "Blockiert: Der Befehl sieht nach einer gefaehrlichen System-/Datentraeger-Aktion aus."
    if any(x in lowered for x in ["\\windows\\system32", "c:\\windows", "%windir%"]):
        if re.search(r"\b(del|erase|move|copy|ren|rename|rmdir|rd|remove-item)\b", lowered):
            return "Blockiert: Schreib-/Loeschaktion im Windows-Systembereich."
    return None
