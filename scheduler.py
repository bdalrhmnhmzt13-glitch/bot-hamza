#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جدولة المهام
"""
from telegram.ext import ContextTypes

from config import config, logger
from utils import hadith_manager


async def send_hadith(context: ContextTypes.DEFAULT_TYPE):
    """إرسال حديث للقناة"""
    try:
        hadith = hadith_manager.get_random()
        message = hadith_manager.format_safe(hadith)
        
        await context.bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=message
        )
        
        logger.info("✅ تم إرسال حديث للقناة")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الحديث: {e}")