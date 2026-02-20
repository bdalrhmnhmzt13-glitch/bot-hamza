#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.request import HTTPXRequest
import messages

# تحميل المتغيرات من ملف .env
load_dotenv()

# قراءة التوكن من متغير البيئة
TOKEN = os.getenv("TOKEN")

# معرف القناة الصحيح (عدلته)
CHANNEL_ID = -1002505073308

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

# معرف المشرف (ضع معرفك هنا)
ADMIN_IDS = [6604637783]  # المعرف الذي ظهر في اللوق

# حالات المحادثة
WAITING_FOR_IMAGE = 1
WAITING_FOR_POST = 2

# ==================== دوال مساعدة ====================

def safe_markdown(text):
    """إزالة علامات Markdown التي قد تسبب مشاكل"""
    if not text:
        return text
    # استبدال العلامات الخاصة
    text = text.replace('_', '\\_')
    text = text.replace('*', '\\*')
    text = text.replace('`', '\\`')
    text = text.replace('[', '\\[')
    return text

def get_random_hadith():
    """اختيار حديث عشوائي من قائمة الأحاديث في messages.py"""
    return random.choice(messages.AHADITH)

def format_hadith(hadith):
    """تنسيق الحديث للعرض مع معالجة Markdown"""
    return messages.HADITH_TEMPLATE.format(
        text=hadith['text'],
        source=hadith['source'],
        explanation=hadith['explanation'],
        time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

# ==================== دوال البوت الأساسية ====================

async def send_hadith(context: ContextTypes.DEFAULT_TYPE):
    """إرسال حديث للقناة - نسخة آمنة بدون Markdown"""
    try:
        hadith = get_random_hadith()
        
        # إنشاء نص بدون أي علامات Markdown
        message = f"""
🕌 حديث نبوي شريف

📖 {hadith['text']}

📚 المصدر: {hadith['source']}
💡 شرح: {hadith['explanation']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤲 تم النشر بواسطة بوت hamza_Root
"""
        
        # إرسال بدون parse_mode
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message
        )

        logger.info("✅ تم إرسال حديث جديد للقناة")
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الحديث للقناة: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user = update.effective_user
    logger.info(f"✅ مستخدم جديد: {user.id} - {user.first_name}")
    
    # رسالة ترحيب مخصصة
    welcome = messages.WELCOME_MESSAGE
    
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def hadith_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /hadith - إرسال حديث فوري"""
    try:
        hadith = get_random_hadith()
        message = format_hadith(hadith)
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"✅ تم إرسال حديث للمستخدم {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الحديث للمستخدم: {e}")
        await update.message.reply_text(messages.ERROR_MESSAGE)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /about"""
    await update.message.reply_text(messages.ABOUT_MESSAGE, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    await update.message.reply_text(messages.HELP_MESSAGE, parse_mode='Markdown')

async def test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /test - اختبار إرسال للقناة"""
    try:
        test_message = f"""
🧪 رسالة اختبار من البوت

✅ البوت يعمل بشكل صحيح ويمكنه إرسال الرسائل للقناة.

📊 معلومات القناة:
• المعرف: {CHANNEL_ID}
• الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

👨‍💻 المطور: hamza_Root
"""
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=test_message
        )
        
        await update.message.reply_text("✅ تم إرسال رسالة اختبار للقناة بنجاح")
        logger.info("✅ تم إرسال رسالة اختبار للقناة")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")
        logger.error(f"❌ خطأ في اختبار القناة: {e}")

# ==================== دوال لوحة التحكم ====================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /dashboard - فتح لوحة التحكم"""
    user_id = update.effective_user.id
    
    # التحقق من أن المستخدم مشرف
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ عذراً، هذه اللوحة للمشرفين فقط.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات القناة", callback_data="stats")],
        [InlineKeyboardButton("🖼️ إرسال صورة للقناة", callback_data="send_image")],
        [InlineKeyboardButton("📝 إرسال منشور للقناة", callback_data="send_post")],
        [InlineKeyboardButton("➕ إضافة صورة", callback_data="add_image")],
        [InlineKeyboardButton("✏️ إضافة منشور", callback_data="add_post")],
        [InlineKeyboardButton("📋 عرض المحتويات", callback_data="list_contents")],
        [InlineKeyboardButton("🎲 محتوى عشوائي", callback_data="random_content")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎛️ *لوحة تحكم القناة*\n\nاختر ما تريد القيام به:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return
    
    if query.data == "stats":
        await show_stats(update, context)
    elif query.data == "send_image":
        await send_image_to_channel(update, context)
    elif query.data == "send_post":
        await send_post_to_channel(update, context)
    elif query.data == "add_image":
        await query.edit_message_text("🖼️ أرسل لي الصورة التي تريد إضافتها.")
        return WAITING_FOR_IMAGE
    elif query.data == "add_post":
        await query.edit_message_text("📝 أرسل لي النص الذي تريد إضافته كمنشور.")
        return WAITING_FOR_POST
    elif query.data == "list_contents":
        await list_contents(update, context)
    elif query.data == "random_content":
        await send_random_content(update, context)
    elif query.data == "close":
        await query.edit_message_text("✅ تم إغلاق لوحة التحكم.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات القناة"""
    query = update.callback_query
    try:
        chat = await context.bot.get_chat(CHANNEL_ID)
        
        # محاولة الحصول على عدد الأعضاء
        try:
            members_count = await context.bot.get_chat_member_count(CHANNEL_ID)
            members_text = f"👥 *الأعضاء:* {members_count}"
        except:
            members_text = "👥 *الأعضاء:* غير معروف"
        
        # إحصائيات المكتبة
        images_count = 0
        posts_count = 0
        try:
            import os
            images_count = len([f for f in os.listdir('images') if f.endswith(('.jpg', '.png', '.jpeg'))])
            posts_count = len([f for f in os.listdir('posts') if f.endswith('.txt')])
        except:
            pass
        
        stats_text = f"""
📊 *إحصائيات القناة*

📌 *الاسم:* {chat.title}
🆔 *المعرف:* `{chat.id}`
{members_text}
📝 *الوصف:* {chat.description or 'لا يوجد'}

🖼️ *الصور:* {images_count}
📄 *المنشورات:* {posts_count}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        await query.edit_message_text(f"❌ خطأ: {e}")

async def send_image_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال صورة للقناة"""
    query = update.callback_query
    
    try:
        import os
        import random
        
        images = [f for f in os.listdir('images') if f.endswith(('.jpg', '.png', '.jpeg'))]
        if not images:
            await query.edit_message_text("❌ لا توجد صور في المكتبة. أضف صوراً أولاً.")
            return
        
        image_path = os.path.join('images', random.choice(images))
        
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption="🖼️ *صورة إسلامية*\n\nتم النشر بواسطة البوت",
                parse_mode='Markdown'
            )
        
        await query.edit_message_text("✅ تم إرسال الصورة للقناة بنجاح!")
    except Exception as e:
        await query.edit_message_text(f"❌ خطأ في الإرسال: {e}")

async def send_post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال منشور نصي للقناة"""
    query = update.callback_query
    
    try:
        import os
        import random
        
        posts = [f for f in os.listdir('posts') if f.endswith('.txt')]
        if not posts:
            await query.edit_message_text("❌ لا توجد منشورات. أضف منشورات أولاً.")
            return
        
        post_path = os.path.join('posts', random.choice(posts))
        with open(post_path, 'r', encoding='utf-8') as f:
            post_text = f.read()
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_text,
            parse_mode='Markdown'
        )
        
        await query.edit_message_text("✅ تم إرسال المنشور للقناة بنجاح!")
    except Exception as e:
        await query.edit_message_text(f"❌ خطأ في الإرسال: {e}")

async def list_contents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض محتويات المكتبة"""
    query = update.callback_query
    
    try:
        import os
        
        images = [f for f in os.listdir('images') if f.endswith(('.jpg', '.png', '.jpeg'))]
        posts = [f for f in os.listdir('posts') if f.endswith('.txt')]
        
        text = "📋 *محتويات المكتبة*\n\n"
        text += f"🖼️ *الصور:* {len(images)}\n"
        for img in images[:5]:
            text += f"  • {img}\n"
        
        text += f"\n📄 *المنشورات:* {len(posts)}\n"
        for post in posts[:5]:
            text += f"  • {post}\n"
        
        if len(images) > 5 or len(posts) > 5:
            text += "\n*(يوجد المزيد...)*"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        await query.edit_message_text(f"❌ خطأ: {e}")

async def send_random_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال محتوى عشوائي للقناة"""
    query = update.callback_query
    
    try:
        import os
        import random
        
        # اختيار عشوائي بين صورة أو نص
        choice = random.choice(['image', 'post'])
        
        if choice == 'image':
            images = [f for f in os.listdir('images') if f.endswith(('.jpg', '.png', '.jpeg'))]
            if images:
                image_path = os.path.join('images', random.choice(images))
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=photo,
                        caption="🎲 *محتوى عشوائي*\n\nتم النشر بواسطة البوت",
                        parse_mode='Markdown'
                    )
        else:
            posts = [f for f in os.listdir('posts') if f.endswith('.txt')]
            if posts:
                post_path = os.path.join('posts', random.choice(posts))
                with open(post_path, 'r', encoding='utf-8') as f:
                    post_text = f.read()
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post_text,
                    parse_mode='Markdown'
                )
        
        await query.edit_message_text("✅ تم إرسال محتوى عشوائي للقناة!")
    except Exception as e:
        await query.edit_message_text(f"❌ خطأ: {e}")

# ==================== معالج الأخطاء ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"⚠️ حدث خطأ غير متوقع: {context.error}")

# ==================== الدالة الرئيسية ====================

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # إعدادات الطلب مع timeout أطول
    request = HTTPXRequest(
        connection_pool_size=10,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )
    
    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).request(request).build()

    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)

    # إضافة معالجات الأوامر الأساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", hadith_now))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_channel))
    app.add_handler(CommandHandler("dashboard", dashboard))
    
    # إضافة معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))

    # جدولة إرسال حديث كل ساعة
    app.job_queue.run_repeating(
        send_hadith,
        interval=3600,  # كل ساعة (3600 ثانية)
        first=5,  # بعد 5 ثواني من التشغيل
        name="send_hadith_job"
    )

    logger.info(messages.BOT_STARTED)
    
    # تشغيل البوت
    app.run_polling(timeout=30)

if __name__ == "__main__":
    main()