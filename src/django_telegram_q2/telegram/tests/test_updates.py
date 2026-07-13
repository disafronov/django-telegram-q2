from django.test import SimpleTestCase

from ..updates import TelegramMessage, parse_telegram_update


class TelegramUpdateParserTests(SimpleTestCase):
    def test_normalizes_text_message(self):
        result = parse_telegram_update(
            {
                "message": {
                    "chat": {"id": 42},
                    "message_id": 7,
                    "date": 1700000000,
                    "text": "  hello  ",
                }
            }
        )

        self.assertEqual(
            result,
            TelegramMessage(
                chat_id="42",
                message_id=7,
                date=1700000000,
                text="hello",
            ),
        )

    def test_accepts_string_chat_id_and_missing_message_id(self):
        result = parse_telegram_update(
            {
                "message": {
                    "chat": {"id": "chat"},
                    "date": 1700000000,
                    "text": "hello",
                }
            }
        )

        self.assertEqual(result.message_id if result else None, None)
        self.assertEqual(result.chat_id if result else None, "chat")

    def test_ignores_unsupported_updates(self):
        unsupported = (
            [],
            {},
            {"message": None},
            {"message": {}},
            {"message": {"text": 1}},
            {"message": {"text": "  "}},
            {"message": {"text": "/start"}},
            {"message": {"text": "hello"}},
            {"message": {"text": "hello", "chat": None}},
            {"message": {"text": "hello", "chat": {"id": None}}},
            {"message": {"text": "hello", "chat": {"id": True}}},
            {
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "message_id": "bad",
                }
            },
            {
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "message_id": False,
                }
            },
            {"message": {"text": "hello", "chat": {"id": 1}}},
            {
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "date": False,
                }
            },
        )

        for update in unsupported:
            with self.subTest(update=update):
                self.assertIsNone(parse_telegram_update(update))
