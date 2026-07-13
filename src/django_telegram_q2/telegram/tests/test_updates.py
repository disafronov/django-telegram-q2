from django.test import SimpleTestCase

from ..updates import TelegramMessage, parse_telegram_update


class TelegramUpdateParserTests(SimpleTestCase):
    def test_normalizes_text_message(self):
        result = parse_telegram_update(
            {
                "update_id": 100,
                "message": {
                    "chat": {"id": 42},
                    "message_id": 7,
                    "date": 1700000000,
                    "text": "  hello  ",
                },
            }
        )

        self.assertEqual(
            result,
            TelegramMessage(
                update_id=100,
                chat_id="42",
                message_id=7,
                date=1700000000,
                text="hello",
            ),
        )

    def test_accepts_string_chat_id_and_missing_message_id(self):
        result = parse_telegram_update(
            {
                "update_id": 101,
                "message": {
                    "chat": {"id": "chat"},
                    "date": 1700000000,
                    "text": "hello",
                },
            }
        )

        self.assertEqual(result.message_id if result else None, None)
        self.assertEqual(result.chat_id if result else None, "chat")

    def test_ignores_unsupported_updates(self):
        unsupported = (
            [],
            {},
            {"update_id": True},
            {"update_id": "bad"},
            {"update_id": 1, "message": None},
            {"update_id": 1, "message": {}},
            {"update_id": 1, "message": {"text": 1}},
            {"update_id": 1, "message": {"text": "  "}},
            {"update_id": 1, "message": {"text": "/start"}},
            {"update_id": 1, "message": {"text": "hello"}},
            {"update_id": 1, "message": {"text": "hello", "chat": None}},
            {
                "update_id": 1,
                "message": {"text": "hello", "chat": {"id": None}},
            },
            {
                "update_id": 1,
                "message": {"text": "hello", "chat": {"id": True}},
            },
            {
                "update_id": 1,
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "message_id": "bad",
                },
            },
            {
                "update_id": 1,
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "message_id": False,
                },
            },
            {
                "update_id": 1,
                "message": {"text": "hello", "chat": {"id": 1}},
            },
            {
                "update_id": 1,
                "message": {
                    "text": "hello",
                    "chat": {"id": 1},
                    "date": False,
                },
            },
        )

        for update in unsupported:
            with self.subTest(update=update):
                self.assertIsNone(parse_telegram_update(update))
