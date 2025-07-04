from traceback import format_exc

from asgiref.sync import sync_to_async
from bot.handlers import *
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from telebot.apihelper import ApiTelegramException
from telebot.types import Update

from bot import bot, logger


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}")
    bot.send_message(settings.OWNER_ID, "webhook set")
    return JsonResponse({"message": "OK"}, status=200)


@require_GET
def status(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"message": "OK"}, status=200)


@csrf_exempt
@require_POST
@sync_to_async
def index(request: HttpRequest) -> JsonResponse:
    if request.META.get("CONTENT_TYPE") != "application/json":
        return JsonResponse({"message": "Bad Request"}, status=403)

    json_string = request.body.decode("utf-8")
    update = Update.de_json(json_string)
    try:
        bot.process_new_updates([update])
    except ApiTelegramException as e:
        logger.error(f"Telegram exception. {e} {format_exc()}")
    except ConnectionError as e:
        logger.error(f"Connection error. {e} {format_exc()}")
    except Exception as e:
        bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)


"""Common"""
start = bot.message_handler(commands=['start'])(start)

where_to_go_handler = bot.callback_query_handler(lambda c: c.data=="start_where")(where_to_go_handler)
support_handler = bot.callback_query_handler(lambda c: c.data=="start_support")(support_handler)
how_to_handler = bot.callback_query_handler(lambda c: c.data=="start_how-to")(how_to_handler)

categories_handler = bot.callback_query_handler(lambda c: c.data.startswith("category_"))(categories_handler)

back_handler = bot.callback_query_handler(lambda c: c.data == "back_menu")(back_handler)
check_handler = bot.callback_query_handler(lambda c: c.data == "check")(check_handler)