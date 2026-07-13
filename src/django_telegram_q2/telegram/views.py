"""Webhook views for bot message ingestion."""

import json
import logging

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .intake import accept_telegram_message
from .models import Bot
from .updates import parse_telegram_update

logger = logging.getLogger(__name__)

_SECRET_TOKEN_HEADER = (
    "HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"  # nosec — header name, not a secret value
)


@csrf_exempt
@require_POST
def webhook(request: HttpRequest) -> HttpResponse:
    """Receive Telegram update via webhook and enqueue it as a Job."""
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        logger.warning("Webhook: invalid JSON body")
        return HttpResponse("invalid json", status=400)

    message = parse_telegram_update(body)
    if message is None:
        return HttpResponse("ok")

    secret = request.META.get(_SECRET_TOKEN_HEADER)
    if not secret:
        logger.info("Webhook: missing secret token header")
        return HttpResponse("not found", status=404)

    bot = Bot.objects.filter(enabled=True, webhook_secret=secret).first()

    if bot is None:
        logger.info("Webhook: unverified request")
        return HttpResponse("not found", status=404)

    accept_telegram_message(
        bot,
        message.chat_id,
        message.message_id,
        message.date,
        message.text,
    )

    return HttpResponse("ok")
