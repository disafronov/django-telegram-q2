from unittest.mock import patch

from django.test import TestCase

from ..intake import accept_telegram_update
from ..models import Bot, TelegramUpdateReceipt
from ..updates import TelegramMessage


class TelegramUpdateIntakeTests(TestCase):
    def test_receipt_rolls_back_when_buffer_intake_fails(self):
        bot = Bot.objects.create(
            name="intake-bot",
            telegram_api_token="telegram-token",
        )
        message = TelegramMessage(
            update_id=100,
            chat_id="42",
            message_id=7,
            date=1700000000,
            text="hello",
        )

        with patch(
            "django_telegram_q2.telegram.intake.accept_telegram_message",
            side_effect=RuntimeError("intake failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "intake failed"):
                accept_telegram_update(bot, message)

        self.assertFalse(TelegramUpdateReceipt.objects.exists())
