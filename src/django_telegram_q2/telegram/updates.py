"""Validation and normalization for inbound Telegram updates."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelegramMessage:
    """Normalized text message accepted by the intake pipeline."""

    update_id: int
    chat_id: str
    message_id: int | None
    date: int
    text: str


def parse_telegram_update(update: object) -> TelegramMessage | None:
    """Return a normalized text message, or ``None`` for an ignored update."""
    if not isinstance(update, Mapping):
        return None

    update_id: Any = update.get("update_id")
    if isinstance(update_id, bool) or not isinstance(update_id, int):
        return None

    message = update.get("message")
    if not isinstance(message, Mapping):
        return None

    text = message.get("text")
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text or text.startswith("/"):
        return None

    chat = message.get("chat")
    if not isinstance(chat, Mapping):
        return None
    chat_id: Any = chat.get("id")
    if isinstance(chat_id, bool) or not isinstance(chat_id, (int, str)):
        return None

    message_id: Any = message.get("message_id")
    if message_id is not None and (
        isinstance(message_id, bool) or not isinstance(message_id, int)
    ):
        return None

    message_date: Any = message.get("date")
    if isinstance(message_date, bool) or not isinstance(message_date, int):
        return None

    return TelegramMessage(
        update_id=update_id,
        chat_id=str(chat_id),
        message_id=message_id,
        date=message_date,
        text=text,
    )
