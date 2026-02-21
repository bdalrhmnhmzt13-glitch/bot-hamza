#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from telegram.request import HTTPXRequest

from config import config, logger
from utils import hadith_manager
from admin import (
    dashboard, button_handler, receive_image, receive_post,
    cancel, WAITING_FOR_IMAGE, WAITING_FOR_POST
)
from scheduler import send_hadith

try:
    config.validate()
except ValueError as e:
    logger.critical(f"❌ خطأ في الإعدادات: {e}")
    sys.exit(1)


async def start(update: Update, context):
    from messages import WELCOME_MESSAGE
    user = update.effective_user
    logger.info(f"مستخدم جديد: {user.id} - {user.first_name}")
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode='Markdown')


async def hadith_now(update: Update, context):
    try:
        hadith = hadith_manager.get_random()
        message = hadith_manager.format(hadith)
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"خطأ: {e}")
        from messages import ERROR_MESSAGE
        await update.message.reply_text(ERROR_MESSAGE)


async def about(update: Update, context):
    from messages import ABOUT_MESSAGE
    await update.message.reply_text(ABOUT_MESSAGE, parse_mode='Markdown')


async def help_command(update: Update, context):
    from messages import HELP_MESSAGE
    await update.message.reply_text(HELP_MESSAGE, parse_mode='Markdown')


async def test_channel(update: Update, context):
    try:
        from datetime import datetime
        test_msg = f"🧪 اختبار\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await context.bot.send_message(chat_id=config.CHANNEL_ID, text=test_msg)
        await update.message.reply_text("✅ تم الإرسال!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")


async def error_handler(update: Update, context):
    logger.error(f"⚠️ خطأ: {context.error}", exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ حدث خطأ.")


def main():
    request = HTTPXRequest(
        connection_pool_size=10,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30
    )

    app = ApplicationBuilder().token(config.TOKEN).request(request).build()

    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern='^(add_image|add_post)$')
        ],
        states={
            WAITING_FOR_IMAGE: [MessageHandler(filters.PHOTO, receive_image)],
            WAITING_FOR_POST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_post)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", hadith_now))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_channel))
    app.add_handler(CommandHandler("dashboard", dashboard))

    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(?!add_image|add_post).*$'))

    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(
        send_hadith,
        interval=config.HADITH_INTERVAL,
        first=config.FIRST_DELAY,
        name="hadith_job"
    )

    logger.info("🚀 البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()