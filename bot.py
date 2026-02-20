#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# قراءة التوكن من متغير البيئة
TOKEN = os.getenv("TOKEN")

# التحقق من وجود التوكن
if not TOKEN:
    logging.error("❌ لم يتم تعيين TOKEN في متغيرات البيئة")
    exit(1)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# معرف القناة
CHANNEL_ID = -1003440789169

# قائمة الأحاديث (يمكنك إضافة المزيد)
AHADITH = [
    {
        'text': 'من سلك طريقاً يلتمس فيه علماً سهل الله له به طريقاً إلى الجنة',
        'source': 'رواه مسلم',
        'explanation': 'فضل طلب العلم'
    },
    {
        'text': 'إن الله رفيق يحب الرفق في الأمر كله',
        'source': 'متفق عليه',
        'explanation': 'الرفق والتسامح'
    },
    {
        'text': 'لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه',
        'source': 'البخاري ومسلم',
        'explanation': 'الإيثار وحب الخير'
    },
    {
        'text': 'إنما الأعمال بالنيات وإنما لكل امرئ ما نوى',
        'source': 'متفق عليه',
        'explanation': 'النية والإخلاص'
    },
    {
        'text': 'المسلم من سلم المسلمون من لسانه ويده',
        'source': 'البخاري',
        'explanation': 'صفات المسلم'
    },
    {
        'text': 'تبسمك في وجه أخيك صدقة',
        'source': 'الترمذي',
        'explanation': 'أخلاق المسلم'
    }
]

def get_random_hadith():
    return random.choice(AHADITH)

def format_hadith(hadith):
    return f"""
🕌 *حديث نبوي شريف*

📖 {hadith['text']}

📚 *المصدر:* {hadith['source']}
💡 *شرح:* {hadith['explanation']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

# دالة إرسال الحديث (async)
async def send_hadith(context: ContextTypes.DEFAULT_TYPE):
    try:
        hadith = get_random_hadith()
        message = format_hadith(hadith)

        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode='Markdown'
        )

        logger.info("✅ تم إرسال حديث جديد")
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الحديث: {e}")

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
🌙 *مرحباً بك في بوت الأحاديث النبوية*

هذا البوت يقوم بنشر حديث نبوي شريف كل ساعة في القناة.

🔹 *الأوامر المتاحة:*
/hadith - حديث عشوائي الآن
/about - معلومات عن البوت
/help - قائمة المساعدة
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def hadith_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hadith = get_random_hadith()
        message = format_hadith(hadith)
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"✅ تم إرسال حديث للمستخدم {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الحديث للمستخدم: {e}")
        await update.message.reply_text("عذراً، حدث خطأ. حاول مرة أخرى.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """
🤖 *بوت الأحاديث النبوية*

📌 *الإصدار:* 1.0
🕐 *مميزات البوت:*
• نشر حديث كل ساعة
• إرسال حديث عند الطلب
• شرح مبسط للأحاديث

✨ *تم التطوير باستخدام:* python-telegram-bot
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔹 *قائمة الأوامر:*

/start - بدء استخدام البوت
/hadith - الحصول على حديث عشوائي
/about - معلومات عن البوت
/help - عرض هذه القائمة

📢 *مميزات البوت:*
• يتم إرسال حديث جديد للقناة كل ساعة تلقائياً
• يمكنك طلب حديث في أي وقت باستخدام /hadith
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"⚠️ حدث خطأ: {context.error}")

# الدالة الرئيسية
def main():
    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)

    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", hadith_now))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("انابوت", about))  # تصحيح: بدون مسافة
    app.add_handler(CommandHandler("help", help_command))

    # جدولة إرسال حديث كل ساعة
    app.job_queue.run_repeating(
        send_hadith, 
        interval=3600,  # كل ساعة
        first=5,  # بعد 5 ثواني من التشغيل
        name="send_hadith_job"
    )

    logger.info("🚀 تم تشغيل البوت بنجاح")

    # تشغيل البوت
    app.run_polling()

if __name__ == "__main__":
    main()