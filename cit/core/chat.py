from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatLine:
    sender: str
    text: str
    at: str

    @classmethod
    def make(cls, sender: str, text: str) -> "ChatLine":
        return cls(sender=sender, text=text, at=datetime.now().strftime("%H:%M:%S"))

    def render(self) -> str:
        return f"[{self.at}] {self.sender}: {self.text}"
