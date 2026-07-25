from __future__ import annotations

import socket
import threading
import time
from typing import Callable, Optional

try:
    import numpy as np
    import sounddevice as sd
except Exception:  # Allows Cit GUI to start even without audio deps/devices.
    np = None
    sd = None

SIGNAL_PORT = 50120
AUDIO_PORT = 50121
RATE = 44100
CHUNK = 1024

STATE_IDLE = "idle"
STATE_RINGING = "ringing"
STATE_CALL = "call"

class VoiceClient:
    """LAN voice module adapted from the user's lan_caller.py.

    UDP signaling and raw int16 mono UDP audio. Intended for trusted LAN use.
    """
    def __init__(self, on_status: Callable[[str], None], on_incoming: Callable[[str], bool]):
        self.on_status = on_status
        self.on_incoming = on_incoming
        self.state = STATE_IDLE
        self.peer_ip: Optional[str] = None
        self.input_device = None
        self.output_device = None
        self.signal = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.signal.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.signal.bind(("", SIGNAL_PORT))
        except OSError:
            self.on_status("Sprachchat-Port ist schon belegt.")
        self.audio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener = threading.Thread(target=self._signal_loop, daemon=True)
        self.listener.start()

    def audio_available(self) -> bool:
        return sd is not None and np is not None

    def devices(self):
        if not self.audio_available():
            return [], []
        devices = sd.query_devices()
        mics = [(i, d["name"]) for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0]
        outs = [(i, d["name"]) for i, d in enumerate(devices) if d.get("max_output_channels", 0) > 0]
        return mics, outs

    def set_devices(self, input_device, output_device) -> None:
        self.input_device = input_device
        self.output_device = output_device

    def call(self, ip: str) -> None:
        if self.state != STATE_IDLE:
            self.on_status("Sprachchat ist bereits aktiv oder klingelt.")
            return
        if not self.audio_available():
            self.on_status("Sprachchat nicht gestartet: sounddevice/numpy fehlt.")
            return
        self.peer_ip = ip.strip()
        if not self.peer_ip:
            return
        self.on_status(f"Rufe {self.peer_ip} an ...")
        try:
            self.signal.sendto(b"CALL", (self.peer_ip, SIGNAL_PORT))
        except Exception as e:
            self.on_status(f"Sprachchat-Start fehlgeschlagen: {e}")

    def accept(self) -> None:
        self._start_call(send_accept=True)

    def hangup(self, remote: bool = False) -> None:
        if self.state == STATE_IDLE:
            return
        if not remote and self.peer_ip:
            self.signal.sendto(b"HANGUP", (self.peer_ip, SIGNAL_PORT))
        self.state = STATE_IDLE
        self.on_status("Sprachchat bereit.")

    def _start_call(self, send_accept: bool = False) -> None:
        if not self.audio_available():
            self.on_status("sounddevice/numpy fehlt. Sprachchat nicht verfuegbar.")
            self.state = STATE_IDLE
            return
        if not self.peer_ip or self.state == STATE_CALL:
            return
        self.state = STATE_CALL
        if send_accept:
            try:
                self.signal.sendto(b"ACCEPT", (self.peer_ip, SIGNAL_PORT))
            except Exception as e:
                self.on_status(f"Sprachchat-Antwort fehlgeschlagen: {e}")
        self.on_status(f"Sprachchat verbunden mit {self.peer_ip}")
        threading.Thread(target=self._audio_send, daemon=True).start()
        threading.Thread(target=self._audio_receive, daemon=True).start()

    def _signal_loop(self) -> None:
        while True:
            try:
                data, addr = self.signal.recvfrom(1024)
                msg = data.decode("utf-8", "ignore")
                if msg == "CALL" and self.state == STATE_IDLE:
                    self.peer_ip = addr[0]
                    self.state = STATE_RINGING
                    self.on_status(f"Eingehender Sprachchat von {self.peer_ip}")
                    accept = False
                    try:
                        accept = bool(self.on_incoming(self.peer_ip))
                    except Exception as e:
                        self.on_status(f"Sprachchat-Annahmefehler: {e}")
                    if accept:
                        self.accept()
                    else:
                        self.state = STATE_IDLE
                elif msg == "ACCEPT":
                    self._start_call(send_accept=False)
                elif msg == "HANGUP":
                    self.hangup(remote=True)
            except OSError:
                break
            except Exception as e:
                self.on_status(f"Sprachchat-Fehler: {e}")

    def _audio_send(self) -> None:
        def callback(indata, frames, time_info, status):
            if self.state == STATE_CALL and self.peer_ip:
                try:
                    self.audio.sendto(indata.tobytes(), (self.peer_ip, AUDIO_PORT))
                except OSError:
                    pass
        try:
            with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=CHUNK, device=self.input_device, callback=callback):
                while self.state == STATE_CALL:
                    sd.sleep(100)
        except Exception as e:
            self.on_status(f"Mikrofon-Fehler: {e}")
            self.hangup(remote=False)

    def _audio_receive(self) -> None:
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.bind(("", AUDIO_PORT))
            recv_sock.settimeout(0.03)
        except OSError as e:
            self.on_status(f"Audio-Port-Fehler: {e}")
            return
        def callback(outdata, frames, time_info, status):
            try:
                data, _ = recv_sock.recvfrom(CHUNK * 2)
                arr = np.frombuffer(data[:CHUNK * 2], dtype="int16")
                if arr.size < frames:
                    padded = np.zeros(frames, dtype="int16")
                    padded[:arr.size] = arr
                    arr = padded
                outdata[:] = arr[:frames].reshape(-1, 1)
            except Exception:
                outdata.fill(0)
        try:
            with sd.OutputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=CHUNK, device=self.output_device, callback=callback):
                while self.state == STATE_CALL:
                    sd.sleep(100)
        except Exception as e:
            self.on_status(f"Lautsprecher-Fehler: {e}")
        finally:
            recv_sock.close()
