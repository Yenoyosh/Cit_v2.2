# Cit v2.2

**Cit** ist ein experimentelles LAN-Collaboration-Tool zum gemeinsamen Programmieren im lokalen Netzwerk.

Cit ist **kein Git-Ersatz**, sondern ein direkter gemeinsamer Projekt-Arbeitsbereich für mehrere Geräte im selben Netzwerk. Es kombiniert Projekt-Sync, Mini-Editor, Chat, Whiteboard, Terminal, Bildvorschau, einfache Bildbearbeitung, OpenAI-Unterstützung, Backups, Undo/Redo und Sicherheitsregeln in einer PyQt6-App.

Cit richtet sich besonders an kleine Teams, Freunde, Geschwister, Schulprojekte, LAN-Coding-Sessions oder gemeinsames Basteln an Python-, Rust-, Web-, Assembly- oder anderen Code-Projekten.

---

## Inhaltsverzeichnis

- [Was ist Cit?](#was-ist-cit)
- [Wichtiger Hinweis](#wichtiger-hinweis)
- [Features](#features)
- [Schnellstart](#schnellstart)
- [Installation](#installation)
- [Requirements](#requirements)
- [Workspace-Struktur](#workspace-struktur)
- [Projektordner und Sandbox](#projektordner-und-sandbox)
- [LAN-Verbindung](#lan-verbindung)
- [LAN-Scan und IP-Scan](#lan-scan-und-ip-scan)
- [Multiple Connect](#multiple-connect)
- [Securemode](#securemode)
- [Datei-Sync](#datei-sync)
- [Backups](#backups)
- [Undo und Redo nach Sync](#undo-und-redo-nach-sync)
- [Offline-Arbeiten](#offline-arbeiten)
- [Paralleles Arbeiten an einer Datei](#paralleles-arbeiten-an-einer-datei)
- [Line-Splitting](#line-splitting)
- [Datei-Fokus im Tree-View](#datei-fokus-im-tree-view)
- [Mini-Editor](#mini-editor)
- [Bildvorschau und Bildbearbeitung](#bildvorschau-und-bildbearbeitung)
- [Whiteboard](#whiteboard)
- [Chat](#chat)
- [Terminal und Ausführen](#terminal-und-ausführen)
- [OpenAI-Projektassistent](#openai-projektassistent)
- [skills.txt](#skillstxt)
- [KI-Chatverlauf](#ki-chatverlauf)
- [OpenAI-Dateikommandos](#openai-dateikommandos)
- [Sicherheitsmodell](#sicherheitsmodell)
- [Rechte-System](#rechte-system)
- [Remote-Terminal](#remote-terminal)
- [Ignorierte Dateien](#ignorierte-dateien)
- [cit_id.txt](#cit_idtxt)
- [Typischer Workflow](#typischer-workflow)
- [GitHub-Hinweis](#github-hinweis)
- [Haftungsausschluss](#haftungsausschluss)
- [Lizenz](#lizenz)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Roadmap-Ideen](#roadmap-ideen)
- [Kurz gesagt](#kurz-gesagt)

---

## Was ist Cit?

Cit ist ein Tool, mit dem mehrere Personen im gleichen lokalen Netzwerk gemeinsam an einem Projekt arbeiten können.

Die Grundidee:

```text
Ein Gerät erstellt oder hostet ein Cit-Projekt.
Andere Geräte im LAN verbinden sich damit.
Alle arbeiten am gleichen Projekt.
Cit synchronisiert die Dateien im Hintergrund.
```

Man kann dabei weiterhin externe Editoren benutzen, zum Beispiel:

```text
- IDLE
- VS Code
- PyCharm
- Notepad++
- normaler Explorer
- andere Editoren
```

Cit selbst ist also nicht nur eine IDE, sondern eher ein:

```text
LAN-Projekt-Sync-Tool
+ Mini-Editor
+ Chat
+ Whiteboard
+ Terminal
+ KI-Projektassistent
+ Backup-/Undo-System
+ Sicherheitslayer
```

Cit soll das gemeinsame Arbeiten an Projekten im LAN einfacher machen, ohne dass man ständig Dateien manüll hin und her kopieren oder zwei Versionen später kompliziert zusammenführen muss.

---

## Wichtiger Hinweis

Cit kann Dateien schreiben, überschreiben, löschen, synchronisieren und Programme starten.

Nutze Cit nur mit Personen und Geräten, denen du vertraust.

Vor Tests mit wichtigen Projekten immer ein externes Backup machen.

Cit ist experimentell. Es kann Fehler geben. Es ist nicht für unersetzliche Projekte ohne zusätzliche Sicherung gedacht.

---

## Features

Cit v2.2 enthält unter anderem:

```text
- Moderne PyQt6-GUI
- Projektverwaltung unter C:\Users\<name>\.cit\projects\
- LAN-Scan
- Direkter IP-Scan
- Verbesserter Scan über Broadcast und lokale Netzwerkprüfung
- Multiple Connect mit bis zu 10 Gegenstellen
- Securemode
- Datei-Sync
- Manüller Sync
- Auto-Sync
- Sync beim Dateiswitch
- Optionales Backup direkt vor Sync
- Manülle Backups
- Undo nach Sync
- Redo nach Sync-Undo
- Mini-Editor
- Dateibaum
- Datei-Fokus-Anzeige
- Paralleles Arbeiten an Dateien
- Line-Splitting
- Temporäre Split-Dateien unter .cit\tmp\lns
- Chat
- Whiteboard
- Bildvorschau
- einfache Bildbearbeitung
- Terminal
- Ausführen-Tab
- gefährliche Terminalbefehle blockiert
- OpenAI-Bot-Tab
- skills.txt im Code
- KI-Chatverlauf pro Projekt
- sichere Datei-Kommandos für den Bot
- Projekt-Sandbox
- Rechte-System
- LICENSE
- SECURITY.md
- cit_logo.png als App-Logo
```

---

## Schnellstart

Unter Windows:

```bat
start_cit.bat
```

Die Batch-Datei zeigt:

```text
[1/2] Installiere Module...
[2/2] Starte Cit...
```

Manüll:

```bat
python -m pip install -r requirements.txt
python -m cit.main
```

Empfohlen mit virtüller Umgebung:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m cit.main
```

---

## Installation

1. ZIP herunterladen oder GitHub-Repo klonen.
2. Ordner öffnen.
3. `start_cit.bat` ausführen.

Oder über CMD:

```bat
cd pfad\zu\cit_v2_0
python -m pip install -r requirements.txt
python -m cit.main
```

Wenn du globale Python-Pakete nicht verändern willst, nutze eine `.venv`:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m cit.main
```

---

## Requirements

```txt
PyQt6>=6.6
sounddevice>=0.4.6
numpy==2.2.6
```

Bedeutung:

```text
PyQt6       GUI
sounddevice Sprachchat / Audio-Basis
numpy       Audio-Puffer / Verarbeitung
```

Wenn du Paketkonflikte mit anderen Python-Projekten hast, nutze unbedingt eine virtülle Umgebung.

---

## Workspace-Struktur

Cit arbeitet standardmäßig in:

```text
C:\Users\<name>\.cit\
```

Wichtige Ordner:

```text
.cit\projects\<projektname>\        echte Projektordner
.cit\exec_local\<cit-id>\           lokale Ausführ-Kopie
.cit\working\<cit-id>\              Working-Kopie nach Verbindungsende
.cit\backups\<cit-id>\              manülle Backups
.cit\sync_state\<cit-id>\           Sync-Zustand
.cit\tmp\lns\                       temporäre Line-Split-Dateien
.cit\ai_chats\<cit-id>\             KI-Chatverlauf pro Projekt
```

Jedes Projekt bekommt eine Datei:

```text
cit_id.txt
```

Diese Datei ist wichtig und darf nicht gelöscht werden.

---

## Projektordner und Sandbox

Cit darf nur innerhalb des aktiven Projektordners arbeiten.

Beispiel:

```text
C:\Users\<name>\.cit\projects\meinprojekt\
```

Erlaubt:

```text
main.py
src/game.py
assets/logo.png
docs/readme.txt
unterordner/datei.txt
```

Blockiert:

```text
..\..\Desktop\passwort.txt
C:\Windows\System32\...
C:\Users\<name>\Documents\...
absolute Pfade
Pfade mit ..
```

Diese Sandbox gilt für:

```text
- normalen Sync
- Dateioperationen
- OpenAI-Dateikommandos
- Löschen
- Verschieben
- Umbenennen
- Terminal-nahe Aktionen, soweit kontrollierbar
```

Die GUI alleine ist dabei nicht die Sicherheitsgrenze. Dateioperationen müssen auch im Netzwerk- und Datei-Code geprüft werden.

---

## LAN-Verbindung

Cit kann Projekte im lokalen Netzwerk finden und verbinden.

Ablauf:

```text
1. Person A erstellt/öffnet ein Cit-Projekt.
2. Person B scannt im LAN oder gibt direkt die IP ein.
3. Cit findet das Projekt.
4. Person B fragt Verbindung an.
5. Host bekommt eine Warnung mit IP.
6. Host akzeptiert oder lehnt ab.
7. Nach Akzeptieren werden Chat, Sync und Projektzugriff aktiv.
```

Beim Verbinden soll klar sichtbar sein:

```text
- welche IP sich verbinden will
- welches Projekt angefragt wird
- welche Rechte vergeben werden
- dass Zugriff auf Projektdateien gefährlich sein kann
```

---

## LAN-Scan und IP-Scan

Cit unterstützt mehrere Scan-Arten.

### 1. LAN-Scan

Cit sucht automatisch nach Cit-Projekten im lokalen Netzwerk.

Das kann durch Windows-Firewall, Router oder Netzwerkeinstellungen manchmal blockiert werden.

### 2. Direkter IP-Scan

Wenn Broadcast/LAN-Scan nichts findet, kann man eine bestimmte IP scannen.

Beispiel:

```text
192.168.2.104
```

Das ist oft zuverlässiger als Broadcast.

### 3. Verbesserte lokale Prüfung

Cit v2.2 nutzt zusätzlich eine robustere Scan-Logik:

```text
- Broadcast-Scan
- direkter IP-Scan
- lokale /24-Prüfung
```

Dadurch sollen Projekte im gleichen Netzwerk zuverlässiger gefunden werden.

Wenn der allgemeine LAN-Scan nichts findet, aber der IP-Scan funktioniert, liegt es meistens an Firewall-, Router- oder Broadcast-Einstellungen.

---

## Multiple Connect

Cit kann sich mit bis zu 10 anderen Gegenstellen verbinden.

Dadurch können mehrere Personen gleichzeitig an einem Projekt arbeiten.

Funktionen mit mehreren Verbindungen:

```text
- Chat an alle
- Sync an alle
- Datei-Fokus an alle
- Whiteboard senden
- Dateioperationen verteilen
- Locks/Fokus anzeigen
```

Der Host kann Verbindungen ablehnen, wenn zu viele Gegenstellen aktiv sind.

---

## Securemode

Securemode bedeutet:

```text
Nur IPs aus dem gleichen Netzwerk werden akzeptiert.
```

Außerdem gilt:

```text
Remote-Terminal ist im Securemode automatisch aus.
```

Securemode ist als sicherere Standardoption gedacht.

---

## Datei-Sync

Cit synchronisiert Projektdateien:

```text
- manüll per Button
- automatisch nach bestimmten Aktionen
- optional regelmäßig
- beim Dateiswitch
- nach Dateiänderungen
```

Ziel:

```text
Alle verbundenen Geräte sollen möglichst denselben Projektstand haben.
```

Cit ignoriert typische Müll- und Cache-Dateien, zum Beispiel:

```text
__pycache__/
*.pyc
.venv/
venv/
.git/
dist/
build/
*.log
```

---

## Backups

Cit unterstützt zwei Arten von Backups.

### 1. Manülle Backups

Manülle Backups werden vom Nutzer aktiv erstellt.

Sie liegen unter:

```text
.cit\backups\<cit-id>\
```

### 2. Backup direkt vor Sync

Im LAN/Sync-Tab kann eingestellt werden:

```text
[ ] Vor Sync aktülle Sicherheitskopie speichern
```

Wenn aktiviert:

```text
- Cit speichert direkt vor dem Sync eine Sicherheitsversion
- es wird nur die Version direkt vor dem Sync gesichert
- es entstehen keine endlosen Auto-Backup-Ordner
```

Wenn deaktiviert:

```text
- Cit synct ohne automatisches Vorher-Backup
- manülle Backups bleiben möglich
```

Das Backup direkt vor Sync ist als schnelle Rettung gedacht, falls ein Sync unerwartet falsche Dateien übernimmt.

---

## Undo und Redo nach Sync

Cit v2.2 unterstützt Undo/Redo nach Syncs.

Buttons:

```text
Undo letzter Sync
Redo Sync-Undo
```

Ziel:

```text
Wenn ein Sync Mist gebaut hat, kann man den letzten Sync rückgängig machen.
```

Redo kann einen rückgängig gemachten Sync wiederherstellen.

Das ersetzt kein echtes externes Backup, ist aber ein wichtiges Sicherheitsnetz.

---

## Offline-Arbeiten

Cit unterstützt lokales Weiterarbeiten.

Wenn eine Verbindung beendet wird, kann eine Working-Kopie gespeichert werden:

```text
.cit\working\<cit-id>\
```

Beim nächsten Verbinden erkennt Cit das Projekt über:

```text
cit_id.txt
```

In der aktuellen v2.2-Logik gilt:

```text
Wenn offline editiert wurde und danach gesynct wird,
wird wieder direkt synchronisiert/überschrieben.
```

Es gibt also keine nervige Merge-Frage mehr wie in späteren instabilen Zwischenständen.

Wichtig:

```text
Bei wichtigen Offline-Änderungen vorher Backup machen.
```

---

## Paralleles Arbeiten an einer Datei

Cit soll ermöglichen, dass mehrere Personen möglichst gut parallel an einer Datei arbeiten können.

Dafür nutzt Cit:

```text
- Datei-Fokus
- Markierung im Tree-View
- Line-Splitting
- temporäre Split-Dateien
- Blöcke statt sofort tausende Mini-Dateien
```

Wenn zwei Personen dieselbe Datei fokussieren oder bearbeiten, kann Cit automatisch in den Line-Split-Modus wechseln.

Das Ziel ist:

```text
Mehrere Personen können an derselben Datei arbeiten,
ohne dass sofort der komplette Inhalt überschrieben wird.
```

---

## Line-Splitting

Line-Splitting ist Cits Ansatz, um paralleles Arbeiten an einer Datei zu ermöglichen.

Grundprinzip:

```text
Datei
→ große Blöcke
→ kleinere Blöcke
→ Lines
→ bei Bedarf Chars
```

Wichtig:

```text
Nicht direkt alles in einzelne Zeilen oder Zeichen zerlegen.
Nur dort feiner werden, wo wirklich gleichzeitig gearbeitet wird.
```

Blockgrößen:

```text
kleine Dateien:
  10er-Blöcke

mittlere Dateien:
  100er-Blöcke

große Dateien:
  1000er-Blöcke
```

Temporäre Dateien liegen unter:

```text
.cit\tmp\lns\
```

Nicht im Projektordner.

Nach dem Zusammenfügen werden temporäre Dateien gelöscht.

Jede Line bekommt eine stabile ID, damit Einfügen/Enter oben in der Datei nicht die komplette Zuordnung zerstört.

---

## Datei-Fokus im Tree-View

Cit zeigt an, woran andere gerade arbeiten.

Wenn eine andere Person eine Datei öffnet oder fokussiert:

```text
- Cit sendet ein Fokus-Signal
- dein Tree-View markiert die Datei
- du siehst: jemand arbeitet gerade dort
```

Dadurch erkennt man besser:

```text
Ah, Tim ist gerade in main.py.
```

Das ist besonders wichtig, wenn die andere Person nicht im Cit-Mini-Editor arbeitet, sondern in IDLE, VS Code oder einem anderen Editor.

---

## Mini-Editor

Cit hat einen integrierten Mini-Editor.

Features:

```text
- Dateibaum
- Textdateien öffnen
- Textdateien bearbeiten
- Speichern
- Strg+S
- Neu laden
- extern öffnen
- größere Editor-Fläche im Vollbild
- deaktivierte Felder, wenn kein Projekt gewählt ist
```

Cit ist trotzdem keine vollständige IDE. Der Mini-Editor ist für schnelle Änderungen und Überblick gedacht.

Man kann weiterhin normal in externen Editoren arbeiten.

---

## Bildvorschau und Bildbearbeitung

Cit kann Bilddateien anzeigen:

```text
PNG
JPG
JPEG
GIF
BMP
WEBP
```

Einfache Bildfunktionen:

```text
- Vorschau
- Markieren/Zeichnen
- Drehen
- Spiegeln
- Speichern
```

Bei Bildspeichern wird vorher ein Backup erstellt, wenn aktiviert.

---


## Kamera-Chat

Cit v2.2 unterstützt Kamera-Chat zwischen verbundenen Gegenstellen.

Funktionen:

```text
- lokale Kamera starten/stoppen
- eigene Kamera bewusst im Chat teilen
- Kamera der Gegenstelle anfragen
- Kameras von mehreren Gegenstellen gleichzeitig ansehen
- pro Gegenstelle eigener Kamera-Tab
- Kamera-Vollbild öffnen und wieder schließen
- Chat-Meldung: [KAMERA] <IP> hat die Kamera gestartet/gestoppt
- Kamera-Teilen stoppen
- Snapshot ins Projekt speichern
```

Wichtig:

```text
- Die Kamera wird nicht heimlich gestartet.
- Wenn jemand deine Kamera sehen will, fragt Cit vorher nach.
- Ohne Freigabe wird kein Kamerabild gesendet.
- Wenn eine Kamera gestartet oder gestoppt wird, steht im Chat eine [KAMERA]-Meldung.
- Mehrere Remote-Kameras können parallel in eigenen Tabs angezeigt werden.
- Remote-Kameras können per Doppelklick oder Button im Vollbild angezeigt und wieder geschlossen werden.
- Es wird kein automatischer Internet-Stream erstellt; die Übertragung läuft über die aktive Cit-Verbindung im LAN.
```

## Whiteboard

Cit v2.2 enthält ein Whiteboard.

Damit kann man gemeinsam etwas erklären oder skizzieren.

Features:

```text
- Zeichnen
- Whiteboard leeren
- Whiteboard an verbundene Gegenstellen senden
- Whiteboard als PNG speichern
```

Nützlich für:

```text
- Ideen skizzieren
- Code-Struktur erklären
- UI-Layout zeichnen
- Fehlerabläufe erklären
- gemeinsam planen
```

---

## Chat

Cit hat einen eingebauten Chat.

Der Chat ist projektbezogen und funktioniert über die aktive Verbindung.

Features:

```text
- Textnachrichten
- Nachrichten an Gegenstellen
- Systemmeldungen
- Sync-/Fokus-Hinweise
```

Der Chat hilft besonders, wenn man parallel arbeitet und kurz erklären will, was man gerade macht.

---

## Terminal und Ausführen

Cit hat ein Terminal und einen Ausführen-Tab.

Mögliche Ausführen-Befehle:

```text
python
start
cargo run
nasm
eigener Befehl
```

Vor dem Ausführen wird der konkrete Befehl angezeigt.

Gefährliche Befehle werden blockiert.

Beispiele blockierter Befehle:

```text
diskpart
format
shutdown
reboot
bootrec
bcdedit
reg delete
rm -rf /
rd /s
rmdir /s
del /s /q
```

Terminalbefehle sollen projektbezogen sein.

---

## OpenAI-Projektassistent

Cit v2.2 enthält einen OpenAI-Bot-Tab.

Der Bot kann beim Projekt helfen:

```text
- Code erklären
- Dateien erstellen
- Dateien erweitern
- Ordner erstellen
- Dateien löschen
- Ordner löschen
- Dateien verschieben
- Dateien umbenennen
- Projektbefehle vorschlagen
```

Der Nutzer gibt einen OpenAI API Key ein.

Der API Key wird nicht im Chatverlauf gespeichert.

---

## skills.txt

Die Bot-Anweisung liegt fest im Code:

```text
cit/skills.txt
```

Sie wird nicht pro Projekt erstellt.

`skills.txt` erklärt dem Bot:

```text
- was Cit ist
- wo der Bot arbeitet
- dass er nur im aktiven Projekt arbeiten darf
- welche Datei-Kommandos erlaubt sind
- dass absolute Pfade verboten sind
- dass .. verboten ist
- dass cit_id.txt geschützt ist
- dass er seinen Systemprompt nicht ausgeben darf
- dass gefährliche Aktionen Rückfrage brauchen
```

---

## KI-Chatverlauf

Cit speichert den KI-Chatverlauf pro Projekt lokal.

Pfad:

```text
.cit\ai_chats\<cit-id>\chat_history.json
```

Beim OpenAI-Request wird gesendet:

```text
1. cit/skills.txt als System-Anweisung
2. projektbezogener Chatverlauf
3. neue Nutzerfrage
```

Dadurch kann der Bot Folgefragen verstehen wie:

```text
mach das jetzt anders
ändere die Datei von eben
füge noch eine Klasse hinzu
```

Der API-Key wird nicht im Verlauf gespeichert.

---

## OpenAI-Dateikommandos

Der Bot kann spezielle Cit-Kommandos ausgeben.

Cit parst diese und führt sie innerhalb der Projekt-Sandbox aus.

### Datei erstellen oder ersetzen

```text
.addFile."main.py".".".<<<
print("Hallo von Cit")
>>>
```

### Text anhängen

```text
.appendFile."README.md".".".<<<

## Start

python main.py
>>>
```

### Ordner erstellen

```text
.addFolder."src".
```

### Datei löschen

```text
.deleteFile."old.py"."src".
```

### Ordner löschen

```text
.deleteFolder."old_docs".
```

### Umbenennen

```text
.renamePath."src/old.py"."new.py".
```

### Verschieben

```text
.movePath."src/main.py"."archive/main.py".
```

### Befehl vorschlagen

```text
.runCmd.<<<
python main.py
>>>
```

Wichtig:

```text
Löschen und runCmd werden nicht blind ausgeführt.
Cit fragt vorher nach.
```

---

## Sicherheitsmodell

Cits wichtigste Sicherheitsregel:

```text
Der Host bzw. das Zielgerät entscheidet.
Nicht der Client.
```

Ein manipulierter Client darf also nicht einfach behaupten:

```text
Ich habe Full-Perms.
Ich darf löschen.
Ich darf Remote-Terminal benutzen.
Ich darf außerhalb des Projekts schreiben.
```

Der empfangende PC prüft selbst, ob die Aktion erlaubt ist.

---

## Rechte-System

Cit kennt drei Rechte-Stufen:

```text
Nur lesen
Lesen + Schreiben
Vollzugriff
```

### Nur lesen

```text
- Projekt ansehen
- Chat/Fokus möglich
- keine Schreibaktionen
- kein Löschen
```

### Lesen + Schreiben

```text
- Dateien schreiben
- Dateien empfangen
- Dateien erstellen
- Dateien umbenennen
- Dateien verschieben
- Line-Split/Line-Merge
- kein Löschen
```

### Vollzugriff

```text
- Schreiben
- Erstellen
- Umbenennen
- Verschieben
- Löschen
```

Löschen braucht Vollzugriff.

---

## Remote-Terminal

Remote-Terminal ist besonders gefährlich und deshalb stark eingeschränkt.

Regeln:

```text
- standardmäßig aus
- im Securemode aus
- Ziel-PC muss erlauben
- Ziel-PC muss Befehl bestätigen
- gefährliche Befehle werden trotzdem blockiert
```

Auch bei manipulierten Clients gilt:

```text
Der Ziel-PC entscheidet.
```

---

## Ignorierte Dateien

Cit ignoriert standardmäßig typische Cache- und Build-Dateien:

```text
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
.git/
dist/
build/
*.log
*.tmp
.DS_Store
Thumbs.db
```

Zusätzliche Regeln können in einer `cit_ignore.txt` im Projekt stehen.

---

## cit_id.txt

Jedes Projekt enthält:

```text
cit_id.txt
```

Diese Datei ist wichtig.

Sie speichert die Projekt-ID, damit Cit erkennt:

```text
Dieses lokale Projekt gehört zu diesem Cit-Projekt.
```

Nicht löschen.

Nicht umbenennen.

Nicht verschieben.

Nicht vom Bot bearbeiten lassen.

---

## Typischer Workflow

### Projekt hosten

```text
1. Cit starten.
2. Projekt erstellen oder auswählen.
3. Projekt im LAN anbieten.
4. Andere Person scannt oder gibt IP ein.
5. Anfrage akzeptieren.
6. Rechte wählen.
7. Zusammen arbeiten.
```

### Projekt verbinden

```text
1. Cit starten.
2. LAN-Scan oder IP-Scan.
3. Projekt auswählen.
4. Verbindung anfragen.
5. Nach Akzeptieren wird Projekt geladen.
6. Dateien bearbeiten.
7. Sync läuft im Hintergrund.
```

### Parallel arbeiten

```text
1. Beide öffnen dasselbe Projekt.
2. Cit zeigt, wer auf welcher Datei ist.
3. Wenn beide dieselbe Datei bearbeiten, kann Line-Split aktiv werden.
4. Änderungen werden synchronisiert.
5. Whiteboard/Chat helfen beim Abstimmen.
```

---

## GitHub-Hinweis

Diese ZIP bzw. dieses Repository ist GitHub-ready.

Enthalten:

```text
README.md
LICENSE
SECURITY.md
requirements.txt
start_cit.bat
cit/
cit/skills.txt
cit/assets/cit_logo.png
```

Nicht enthalten:

```text
__pycache__/
*.pyc
cit_logo.ico
temporäre Dateien
lokale .cit-Daten
```

---

## Haftungsausschluss

Cit ist experimentell.

Die Nutzung erfolgt vollständig auf eigene Gefahr.

Der Autor übernimmt keine Haftung für Schäden, insbesondere nicht für:

```text
- beschädigte Dateien
- gelöschte Dateien
- verlorenen Qüllcode
- beschädigte Projekte
- Sync-Fehler
- fehlerhafte Merges
- verlorene Backups
- Python-/Paketprobleme
- Netzwerkprobleme
- Betriebssystemprobleme
- Sicherheitsprobleme
- PC-/Hardware-Schäden
- sonstige Datenverluste
```

Vor der Nutzung mit wichtigen Projekten immer ein externes Backup machen.

---

## Lizenz

Cit steht unter einer nicht-kommerziellen Attribution-Lizenz.

Kurzfassung:

```text
Du darfst Cit nutzen, ansehen, bearbeiten und nicht-kommerziell teilen,
wenn der ursprüngliche Autor genannt wird.
```

Nicht erlaubt ohne ausdrückliche Erlaubnis:

```text
- kommerzielle Nutzung
- Verkauf
- bezahltes Hosting
- Entfernen von Lizenz-/Sicherheitshinweisen
- veränderte Versionen als offizielle unveränderte Cit-Version ausgeben
```

Die vollständigen Regeln stehen in:

```text
LICENSE
```

---

## Bekannte Einschränkungen

Cit ist experimentell und noch kein professionelles Versionskontrollsystem.

Bekannte Einschränkungen:

```text
- Kein Ersatz für Git
- Kein vollständiger Schutz wie VM/Docker
- LAN-Scan kann durch Firewall/Router blockiert werden
- Sync kann bei komplexen parallelen Änderungen Fehler machen
- Line-Splitting ist experimentell
- Remote-Terminal bleibt riskant
- OpenAI-Bot braucht einen API Key
- OpenAI-Funktionen hängen von API/Internet ab
- Kein perfekter Schutz gegen alle manipulierten Clients
```

Trotz Security-Regeln gilt:

```text
Nur mit vertraünswürdigen Leuten im LAN nutzen.
```

---

## Roadmap-Ideen

Mögliche zukünftige Verbesserungen:

```text
- Besserer Diff-Viewer
- noch stabileres Sync-Protokoll
- bessere Konfliktansicht
- Geräte-ID statt nur IP
- Trusted-Peers-Liste
- bessere Projekt-Typ-Erkennung
- Terminal-Ausgabe schöner darstellen
- Whiteboard-Live-Sync
- Chat-Verlauf
- mehr Bildbearbeitungsfunktionen
- Crash-Reporter
- Verbindungsdiagnose
- Plugin-System
- portable Cit-Version
```

---

## Kurz gesagt

Cit v2.2 ist ein experimentelles LAN-Coding-Tool für gemeinsames Arbeiten an Projekten.

Es bietet:

```text
Sync
Mini-Editor
Chat
Whiteboard
Terminal
OpenAI-Bot
Backups
Undo/Redo
Line-Splitting
Sicherheitsregeln
```

Cit soll gemeinsames Programmieren im lokalen Netzwerk einfacher machen — ohne ständig manüll Dateien hin und her zu kopieren.


---

## OpenAI-Bot v2.2 Erweiterung

Der OpenAI-Bot liest seine feste Standard-Anweisung aus `cit/skills.txt`. Diese Datei liegt im Code und wird nicht pro Projekt erzeugt. Beim Request wird zuerst `cit/skills.txt` gesendet, danach der lokale KI-Chatverlauf des Projekts und zuletzt die neue Nutzernachricht.

Neü Bot-Funktionen:

```text
.proj%                       Projektstruktur in den KI-Verlauf schreiben
.contfe."main.py".            Inhalt einer Textdatei in den KI-Verlauf schreiben
.contfe<src/main.py>          alternative Kurzform für Dateiinhalt
~text~<...>                   Inhalt nicht als Cit-Kommando interpretieren
.runCmdReason.<<<...>>>       Pflicht-Begründung für CMD-Befehl
.runCmd.<<<python main.py>>>  Befehl nach Rückfrage im Projekt ausführen
```

Wenn ein vom Bot vorgeschlagener CMD-Befehl bestätigt und ausgeführt wird, speichert Cit `stdout`, `stderr` und den Exit-Code wieder im KI-Chatverlauf. Dadurch kann der Bot beim nächsten Prompt Fehler aus der Programmausgabe analysieren.

Löschen und CMD-Befehle werden nicht blind ausgeführt. Cit fragt vorher nach. Gefährliche Befehle bleiben blockiert.

---

## denyai.txt: KI-Zugriff pro Projekt sperren

Cit unterstützt pro Projekt eine Datei:

```text
denyai.txt
```

Diese Datei liegt direkt im Projektordner, zum Beispiel:

```text
C:\Users\<name>\.cit\projects\meinprojekt\denyai.txt
```

Mit `denyai.txt` kann man Dateien oder Ordner definieren, auf die der OpenAI-Bot keinen Zugriff haben soll.

Beispiel:

```text
# Diese Dateien/Ordner sind für den KI-Bot gesperrt
.env
secrets.txt
private/
*.key
config/local_settings.py
```

Der Bot darf wissen, dass `denyai.txt` existiert, aber er darf die Datei selbst nicht lesen, bearbeiten, löschen, verschieben oder umbenennen.

Gesperrte Dateien/Ordner werden blockiert für:

```text
- .contfe
- .addFile
- .appendFile
- .deleteFile
- .deleteFolder
- .renamePath
- .movePath
- .proj%-Ausgabe
```

Damit kann ein Projekt sensible Dateien aus dem KI-Kontext heraushalten, auch wenn der OpenAI-Bot im Projekt aktiviert ist.

---

## CitShell und git-ähnliche Projekt-Zeitmaschine

Cit v2.2 enthält die neue **CitShell**. Sie ist eine eingebaute Shell in der PyQt6-GUI und bringt mehrere git-ähnliche Funktionen direkt in Cit, ohne GitHub/GitLab-Remote-Plattformen oder Pull-Request-Code-Review nachzubauen.

CitShell ist für lokale Projektgeschichte gedacht:

```text
- Backup/Commit mit Nachricht
- Verlauf anzeigen
- Status anzeigen
- Diff-Zusammenfassung
- Branches erstellen
- Branch wechseln
- einfachen Branch-Merge versuchen
- alte Projektstände wiederherstellen
```

Beispiele:

```text
cit backup "Threejs error gefixed"
cit log
cit status
cit branch test-ui
cit branches
cit checkout main
cit merge test-ui
cit restore <commit-id>
```

`cit backup "Nachricht"` ist dabei bewusst ähnlich wie ein Git-Commit gedacht. Cit speichert einen Snapshot des Projekts mit Zeit, Branch und Beschreibung. Danach kann man im Verlauf sehen, was wann gesichert wurde.

CitShell nutzt jetzt eine schlichte dunkle Terminal-Optik ähnlich Git Bash. Der alte Partikel-Header und der künstliche Fake-Cursor sind entfernt.

Wichtig: CitShell ersetzt Git noch nicht vollständig. Es ist eine lokale Cit-Zeitmaschine für Backups, Branches und Recovery, aber kein Ersatz für GitHub/GitLab, Pull Requests oder professionelles Code-Review.

---

## CitShell als eigenes Programm

Cit v2.2 enthält die CitShell jetzt zusätzlich als eigenes Programm.

Start:

```bat
start_citshell.bat
```

Oder direkt:

```bat
python -m cit.citshell
```

Außerdem liegt eine kleine `cit.bat` im Projektordner. Damit kann man Befehle direkt ausführen:

```bat
cit projects
cit select project "Mein Projekt"
cit backup "Threejs error gefixed"
cit log
cit branches
cit checkout main
```

Wichtig: Die externe CitShell arbeitet immer auf dem aktüll ausgewählten Projekt. Zürst auswählen:

```bat
cit select project "Projektname"
```

Danach funktionieren Backup, Verlauf, Branches, Checkout, Merge und Restore direkt in der Shell.

Die komische Punkt-/Partikel-Leiste aus dem CitShell-Header wurde entfernt. Die CitShell nutzt jetzt eine klarere dunkle Terminal-Optik.


---

## Cit v2.2 CitShell External Branch Navigation

Diese Version erweitert CitShell und die GUI-Branch-Navigation:

- Der alte CitShell-In-App-Terminalbereich wurde entfernt.
- Der CitShell-Menüpunkt/Button startet jetzt nur noch die externe CitShell.
- Die externe CitShell hat keinen dekorativen Punkte-/Partikel-Header mehr.
- Der Prompt nutzt die normale Terminal-Eingabe mit grüner Eingabefarbe statt eines extra Fake-Cursors im Text.
- Branches werden in der GUI wie virtülle Projekte angezeigt, z.B. `test.branch."experiment"`.
- Wenn man so einen Branch links auswählt, navigiert Cit in diesen Branch und stellt dessen Stand im Projektordner her.
- Neür Shell-Befehl: `cit navigate branch "branchname"`.
- Neür Shell-Befehl: `cit promote branch "branchname"`.
- Deutsche Form: `cit nutze branch "branchname" als main version`.

`cit promote branch "branchname"` bzw. `cit nutze branch "branchname" als main version` macht den Branch zur neuen Main-Version. Dabei wird der Branch-Stand in `main` übernommen und der alte Branch-Eintrag entfernt. Die neue Main-Version bleibt natürlich erhalten. Vorher versucht Cit ein Safety-Backup der bisherigen Main-Version anzulegen.


## Cit v2.2: Branches, Commits und CitShell

Diese Version erweitert Cit um eine git-ähnliche lokale Projekt-Zeitmaschine, ohne GitHub-/GitLab-Remote-Plattformen und ohne Pull-Request-/Code-Review-System.

### Branches in der GUI

Branches werden nicht mehr als Fake-Projekte wie `projekt.branch."name"` in der linken Projektliste angezeigt. Stattdessen gibt es einen eigenen Menüpunkt/Tab **Branches**. Dort kann man:

```text
- Branches anzeigen
- Branch erstellen
- Branch öffnen/navigieren
- Branch als neue main-Version nutzen
- Branch mergen
- Commits/Backups anzeigen
- Commit wiederherstellen
```

### Commits / Backups

Cit-Backups funktionieren wie lokale Commits. Man kann mit Beschreibung sichern und später im Verlauf nachsehen, was wann gespeichert wurde.

Beispiel in der CitShell:

```bat
cit backup "Threejs error gefixed"
cit log
cit commits
cit commit <commit-id>
cit navigate commit <commit-id>
```

### CitShell

CitShell ist ein externes Programm. Der CitShell-Tab in der GUI startet nur noch die externe Shell.

Wichtige Befehle:

```bat
cit projects
cit select project "Projektname"
cit backup "Nachricht"
cit log
cit commits
cit commit <commit-id>
cit branch experiment
cit branches
cit checkout experiment
cit navigate branch "experiment"
cit navigate commit <commit-id>
cit merge experiment
cit promote branch "experiment"
cit nutze branch "experiment" als main version
cit restore <commit-id>
```

### Branch als main nutzen

Wenn ein Branch gut ist, kann er zur neuen Main-Version gemacht werden:

```bat
cit promote branch "experiment"
```

oder deutsch:

```bat
cit nutze branch "experiment" als main version
```

Cit versucht vorher ein Safety-Backup der alten main-Version anzulegen. Danach wird der Branch-Eintrag entfernt, aber der übernommene Stand bleibt natürlich als neue main-Version erhalten.

### OpenAI-Bot ohne API-Key

Der OpenAI-Bot nutzt in diesem lokalen Desktop-Build weiterhin einen OpenAI API-Key. Ein normaler ChatGPT-Sign-in ohne API-Key ist in dieser ZIP nicht eingebaut. Grund: Der API-Zugriff wird offiziell über API-Keys/Projektkeys authentifiziert; ein normaler ChatGPT-Login kann nicht einfach lokal als API-Zugang verwendet werden.

---

## Cit v2.2: Shell-Optik und Projektveränderungen

Diese Version ändert die CitShell und die Projekt-History-Ansicht:

- Der alte dekorative CitShell-Header mit Punkten/Partikeln wurde entfernt.
- Der CitShell-Tab in der GUI startet nur noch das externe CitShell-Programm.
- Die externe CitShell nutzt eine schlichte dunkle Terminal-Optik ähnlich Git Bash.
- Es gibt keinen künstlichen Fake-Cursor mehr; die Eingabe läuft über den normalen grünen Terminal-Prompt.
- Neuer GUI-Tab **Projektveränderungen**:
  - aktueller Branch
  - HEAD-Commit
  - Status seit letztem Cit-Backup
  - Diff-Zusammenfassung
  - Branch-Liste
  - Commits/Backups mit Beschreibung
  - Commit/Backup erstellen
  - Commit wiederherstellen
- Der OpenAI-Tab enthält keinen „Ohne API-Key / Sign-in?“-Button mehr, weil lokale OpenAI-API-Nutzung in dieser Version über einen API-Key läuft.



---

## Cit v2.2 QUALITY CAMERA-CHAT

Cit v2.2 konzentriert sich auf Qualität, Stabilität und bessere Zusammenarbeit mit externen Editoren.

Neue/verbesserte Punkte:

```text
- Crash-Logs unter .cit\logs\
- Verbindungstest/Diagnose im LAN/Sync-Tab
- Sync-Hashprüfung bei Dateiübertragungen
- erweiterter Health Check / Self-Test
- externe Editor-Änderungen werden erkannt
- bei parallelem Editieren in externen Editoren startet automatisch Line-Split
- Kamera-Tab mit lokaler Webcam-Vorschau
- Kamera-Snapshot kann ins Projekt gespeichert werden
- Branches lassen sich im Branches-Tab per Öffnen/Doppelklick richtig navigieren
- PNG-Mal-/Bildbearbeitung im Editor entfernt
- Bildvorschau bleibt erhalten
- CHANGELOG.md hinzugefügt
```

Hinweis zur Kamera:

```text
Die Kamera nutzt optional opencv-python.
Wenn keine Kamera verfügbar ist oder Windows den Zugriff blockiert, zeigt Cit eine Meldung.
Es wird kein automatischer Kamerastream an andere Geräte gesendet.
Snapshots werden nur lokal gespeichert, wenn der Nutzer den Button nutzt.
```
