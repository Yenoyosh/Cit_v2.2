from __future__ import annotations

import json
import os
import shlex
import sys
import getpass
import socket
from pathlib import Path

from .core.workspace import ensure_workspace, list_projects, project_path, read_project_id
from .core.history import (
    branches as cit_branches,
    checkout_branch,
    create_branch,
    create_commit,
    current_branch,
    diff_summary,
    list_commits,
    commit_meta,
    merge_branch,
    promote_branch_to_main,
    restore_commit,
    status as cit_status,
)

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAG = "\033[95m"
WHITE = "\033[97m"
BLINK = "\033[5m"


def color(text: str, c: str) -> str:
    return f"{c}{text}{RESET}"


def state_path() -> Path:
    root = Path.home() / ".cit"
    root.mkdir(parents=True, exist_ok=True)
    return root / "citshell_state.json"


def load_state() -> dict:
    p = state_path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {"selected_project": ""}


def save_state(data: dict) -> None:
    state_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def selected_project_root() -> Path | None:
    name = load_state().get("selected_project") or ""
    if not name:
        return None
    root = project_path(name)
    if root.exists():
        return root
    return None


def print_header() -> None:
    # Absichtlich schlicht wie Git Bash: kein alter Deko-Header, keine Punkte-Leiste, kein Fake-Cursor.
    print(color("CitShell v2.2", CYAN + BOLD))


def project_label(root: Path | None) -> str:
    if not root:
        return color("~", YELLOW)
    try:
        br = current_branch(root)
    except Exception:
        br = "main"
    return f"{color(root.name, YELLOW)} {color('('+br+')', MAG)}"


def parse_message(raw: str, keyword: str) -> str:
    # keeps quoted text as a message while preserving spaces
    try:
        parts = shlex.split(raw)
        if len(parts) > 2:
            return " ".join(parts[2:]).strip()
    except Exception:
        pass
    return raw.split(keyword, 1)[1].strip().strip('"') or "Cit backup"


def list_projects_text() -> str:
    names = list_projects()
    if not names:
        return "Keine lokalen Cit-Projekte gefunden."
    selected = load_state().get("selected_project") or ""
    lines = ["Lokale Cit-Projekte:"]
    for name in names:
        root = project_path(name)
        marker = "*" if name == selected else " "
        try:
            pid = read_project_id(root)
        except Exception:
            pid = "?"
        lines.append(f"{marker} {name}  ({pid})")
    return "\n".join(lines)


def run_command(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.lower() in ("exit", "quit", "q"):
        raise SystemExit
    if not raw.lower().startswith("cit"):
        return "Befehl muss mit 'cit' starten. Beispiel: cit help"
    try:
        parts = shlex.split(raw)
    except Exception:
        parts = raw.split()
    if len(parts) == 1 or parts[1].lower() in ("help", "?"):
        return help_text()

    cmd = parts[1].lower()

    if cmd in ("projects", "projectlist"):
        return list_projects_text()

    if cmd == "select":
        if len(parts) >= 4 and parts[2].lower() == "project":
            name = parts[3]
        elif len(parts) >= 3:
            name = parts[2]
        else:
            return 'Nutzung: cit select project "Projektname"'
        names = list_projects()
        if name not in names:
            # case-insensitive convenience
            match = next((n for n in names if n.lower() == name.lower()), None)
            if not match:
                return f"Projekt nicht gefunden: {name}\n\n{list_projects_text()}"
            name = match
        state = load_state()
        state["selected_project"] = name
        save_state(state)
        root = project_path(name)
        return f"Projekt ausgewählt: {name}\nPfad: {root}\nBranch: {current_branch(root)}"

    root = selected_project_root()
    if root is None:
        return 'Kein Projekt ausgewählt. Nutze zuerst: cit select project "Projektname"\nOder: cit projects'

    if cmd in ("backup", "commit", "save"):
        msg = parse_message(raw, parts[1]) if len(parts) >= 2 else "Cit backup"
        meta = create_commit(root, msg)
        return f"Backup/Commit erstellt: {meta['id']}\nBranch: {meta['branch']}\nNachricht: {meta['message']}"

    if cmd in ("log", "history", "verlauf", "commits"):
        commits = list_commits(root, 120)
        if not commits:
            return 'Noch kein Cit-Verlauf. Nutze: cit backup "Nachricht"'
        lines = ["Cit-Verlauf / Commits:"]
        for c in commits:
            lines.append(f"{c.get('id')}  [{c.get('branch')}]  {c.get('time')}  - {c.get('message')}")
        return "\n".join(lines)

    if cmd in ("commit", "show"):
        if len(parts) < 3:
            return "Nutzung: cit commit <commit-id>"
        meta = commit_meta(root, parts[2])
        lines = [
            f"Commit: {meta.get('id')}",
            f"Branch: {meta.get('branch')}",
            f"Zeit:   {meta.get('time')}",
            f"Parent: {meta.get('parent') or '-'}",
            f"Text:   {meta.get('message')}",
            "",
            "Dateien:",
        ]
        manifest = meta.get('manifest', {}) or {}
        for rel in sorted(manifest)[:120]:
            lines.append("  " + rel)
        if len(manifest) > 120:
            lines.append(f"  ... {len(manifest)-120} weitere Dateien")
        return "\n".join(lines)

    if cmd == "status":
        st = cit_status(root)
        br = current_branch(root)
        lines = [f"Projekt: {root.name}", f"Branch: {br}", f"HEAD: {st.get('head') or '-'}"]
        if st.get("clean"):
            lines.append("Arbeitsbaum sauber. Keine Unterschiede zum letzten Cit-Backup.")
        else:
            lines.append("Unterschiede seit letztem Cit-Backup:")
            lines.extend(diff_summary(root))
        return "\n".join(lines)

    if cmd == "diff":
        commit_id = parts[2] if len(parts) > 2 else None
        return "\n".join(diff_summary(root, commit_id))

    if cmd in ("branches", "branchlist"):
        cur, brs = cit_branches(root)
        lines = ["Branches:"]
        for name, head in sorted(brs.items()):
            prefix = "*" if name == cur else " "
            lines.append(f"{prefix} {name} -> {head or '-'}")
        return "\n".join(lines)

    if cmd == "branch":
        if len(parts) < 3:
            return "Nutzung: cit branch <name>"
        create_branch(root, parts[2])
        return f"Branch erstellt: {parts[2]}"

    if cmd in ("checkout", "switch"):
        if len(parts) < 3:
            return "Nutzung: cit checkout <branch>"
        checkout_branch(root, parts[2])
        return f"Branch ausgecheckt: {parts[2]}"

    if cmd == "navigate" and len(parts) >= 4 and parts[2].lower() == "branch":
        checkout_branch(root, parts[3])
        return f"Navigiere in Branch: {parts[3]}\nDieser Branch ist jetzt im Projektordner aktiv."

    if cmd == "navigate" and len(parts) >= 4 and parts[2].lower() in ("commit", "backup"):
        answer = input(color(f"Projekt wirklich auf Commit {parts[3]} setzen? Vorher wird ein Safety-Backup erstellt. [y/N] ", YELLOW))
        if answer.strip().lower() not in ("y", "yes", "j", "ja"):
            return "Commit-Navigation abgebrochen."
        create_commit(root, "Auto-Safety vor navigate commit")
        restore_commit(root, parts[3])
        return f"Navigiere in Commit: {parts[3]}\nDieser Commit ist jetzt im Projektordner aktiv."

    if cmd == "nutze":
        # Deutsche Kurzform: cit nutze branch "name" als main version
        if len(parts) >= 6 and parts[2].lower() == "branch" and "main" in [x.lower() for x in parts]:
            target = parts[3]
            return "\n".join(promote_branch_to_main(root, target))

    if cmd == "use":
        # Englisch: cit use branch "name" as main version
        if len(parts) >= 6 and parts[2].lower() == "branch" and "main" in [x.lower() for x in parts]:
            target = parts[3]
            return "\n".join(promote_branch_to_main(root, target))

    if cmd == "promote":
        # cit promote branch "name"
        if len(parts) >= 4 and parts[2].lower() == "branch":
            return "\n".join(promote_branch_to_main(root, parts[3]))
        return 'Nutzung: cit promote branch "branchname"'

    if cmd in ("restore", "revert"):
        if len(parts) < 3:
            return "Nutzung: cit restore <commit-id>"
        answer = input(color(f"Projekt wirklich auf Commit {parts[2]} zurücksetzen? Vorher wird ein Safety-Backup erstellt. [y/N] ", YELLOW))
        if answer.strip().lower() not in ("y", "yes", "j", "ja"):
            return "Restore abgebrochen."
        create_commit(root, "Auto-Safety vor restore")
        restore_commit(root, parts[2])
        return f"Projekt auf Commit zurückgesetzt: {parts[2]}"

    if cmd == "merge":
        if len(parts) < 3:
            return "Nutzung: cit merge <branch>"
        return "\n".join(merge_branch(root, parts[2]))

    if cmd in ("where", "pwd"):
        return str(root)

    return "Unbekannter CitShell-Befehl. Tippe: cit help"


def help_text() -> str:
    return """CitShell Befehle:
  cit projects                 lokale Projekte anzeigen
  cit select project "Name"    Projekt für diese Shell auswählen
  cit backup "Nachricht"       Snapshot/Commit mit Beschreibung erstellen
  cit log | cit history         Verlauf/Commits anzeigen
  cit commits                   Commits anzeigen
  cit commit <commit-id>        Commit-Details und enthaltene Dateien anzeigen
  cit status                    Unterschiede seit letztem Backup anzeigen
  cit diff [commit-id]          Diff-Zusammenfassung anzeigen
  cit branch <name>             Branch erstellen
  cit branches                  Branches anzeigen
  cit checkout <name>           Branch wechseln und Stand wiederherstellen
  cit navigate branch "name"    In Branch navigieren und Stand aktivieren
  cit navigate commit <id>      In alten Commit/Backup navigieren und Stand aktivieren
  cit merge <branch>            Branch in aktuellen Stand holen; Konflikte als *_MERGE_* sichern
  cit promote branch "name"     Branch als neue main-Version übernehmen und Branch-Eintrag löschen
  cit nutze branch "name" als main version
                                Deutsche Form für promote branch
  cit restore <commit-id>       Projekt auf alten Stand zurücksetzen
  cit where                     Projektpfad anzeigen
  exit                          CitShell beenden

Beispiele:
  cit select project "Mein Projekt"
  cit backup "Threejs error gefixed"
  cit branch experiment
  cit checkout experiment
  cit navigate branch "experiment"
  cit navigate commit 20260709_123456_abcd1234
  cit promote branch "experiment"
  cit log
""".rstrip()


def interactive() -> int:
    ensure_workspace()
    print_header()
    print(color("Tippe 'cit help'. Beenden mit 'exit'.", DIM))
    while True:
        root = selected_project_root()
        try:
            user = getpass.getuser()
            host = socket.gethostname()
            loc = project_label(root)
            prompt = f"{color(user + '@' + host, GREEN)} {color('CitShell', MAG)} {loc}\n{color('$', GREEN)} "
            raw = input(prompt)
            print(RESET, end="")
            out = run_command(raw)
            if out:
                print(out)
        except (KeyboardInterrupt, EOFError):
            print("\nbye")
            return 0
        except SystemExit:
            print("bye")
            return 0
        except Exception as e:
            print(color(f"FEHLER: {e}", RED))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ensure_workspace()
    if argv:
        try:
            out = run_command("cit " + " ".join(shlex.quote(a) for a in argv) if argv[0] != "cit" else " ".join(argv))
            if out:
                print(out)
            return 0
        except Exception as e:
            print(color(f"FEHLER: {e}", RED), file=sys.stderr)
            return 1
    return interactive()


if __name__ == "__main__":
    raise SystemExit(main())
