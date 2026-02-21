#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لوحة تحكم المشرف
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import config, logger
from utils import content_manager, MarkdownHelper

# حالات المحادثة
WAITING_FOR_IMAGE = 1
WAITING_FOR_POST = 2


def is_admin(user_id: int) -> bool:
    """التحقق من المشرف"""
    return user_id in config.ADMIN_IDS


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح لوحة التحكم"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ عذراً، هذه اللوحة للمشرفين فقط.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🖼️ إرسال صورة", callback_data="send_image")],
        [InlineKeyboardButton("📝 إرسال منشور", callback_data="send_post")],
        [InlineKeyboardButton("➕ إضافة صورة", callback_data="add_image")],
        [InlineKeyboardButton("✏️ إضافة منشور", callback_data="add_post")],
        [InlineKeyboardButton("📋 عرض المحتوى", callback_data="list_contents")],
        [InlineKeyboardButton("🎲 محتوى عشوائي", callback_data="random_content")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ]
    
    await update.message.reply_text(
        "🎛️ *لوحة تحكم القناة*\n\nاختر ما تريد القيام به:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return ConversationHandler.END
    
    data = query.data
    
    handlers = {
        'stats': show_stats,
        'send_image': send_image,
        'send_post': send_post,
        'add_image': request_image,
        'add_post': request_post,
        'list_contents': list_contents,
        'random_content': send_random,
        'close': close_dashboard,
        'back': dashboard_callback
    }
    
    handler = handlers.get(data)
    if handler:
        return await handler(update, context)
    
    return ConversationHandler.END


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات"""
    query = update.callback_query
    
    try:
        chat = await context.bot.get_chat(config.CHANNEL_ID)
        
        # عدد الأعضاء
        try:
            members = await context.bot.get_chat_member_count(config.CHANNEL_ID)
            members_text = f"👥 *الأعضاء:* {members}"
        except Exception:
            members_text = "👥 *الأعضاء:* غير متاح"
        
        # إحصائيات المحتوى
        stats = content_manager.get_stats()
        
        text = f"""
📊 *إحصائيات القناة*

📌 *الاسم:* {MarkdownHelper.escape(chat.title or 'غير معروف')}
🆔 *المعرف:* `{chat.id}`
{members_text}
📝 *الوصف:* {MarkdownHelper.escape(chat.description or 'لا يوجد')}

📦 *المحتوى:*
🖼️ صور: {stats['images']}
📄 منشورات: {stats['posts']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await query.edit_message_text(f"❌ خطأ: {str(e)}")


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال صورة للقناة"""
    query = update.callback_query
    
    image_path = content_manager.get_random_image()
    if not image_path:
        await query.edit_message_text("❌ لا توجد صور في المكتبة.")
        return ConversationHandler.END
    
    try:
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=config.CHANNEL_ID,
                photo=photo,
                caption="🖼️ *صورة إسلامية*\n\nتم النشر بواسطة البوت",
                parse_mode='Markdown'
            )
        await query.edit_message_text("✅ تم إرسال الصورة بنجاح!")
    except Exception as e:
        logger.error(f"Error sending image: {e}")
        await query.edit_message_text(f"❌ خطأ في الإرسال: {str(e)}")
    
    return ConversationHandler.END


async def send_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال منشور للقناة"""
    query = update.callback_query
    
    post_text = content_manager.get_random_post()
    if not post_text:
        await query.edit_message_text("❌ لا توجد منشورات في المكتبة.")
        return ConversationHandler.END
    
    try:
        await context.bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=post_text[:4096],  # Telegram limit
            parse_mode='Markdown'
        )
        await query.edit_message_text("✅ تم إرسال المنشور بنجاح!")
    except Exception as e:
        logger.error(f"Error sending post: {e}")
        await query.edit_message_text(f"❌ خطأ في الإرسال: {str(e)}")
    
    return ConversationHandler.END


async def request_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب صورة من المستخدم"""
    query = update.callback_query
    await query.edit_message_text("🖼️ أرسل لي الصورة الآن (أو /cancel للإلغاء):")
    return WAITING_FOR_IMAGE


async def request_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب منشور من المستخدم"""
    query = update.callback_query
    await query.edit_message_text("📝 أرسل لي نص المنشور الآن (أو /cancel للإلغاء):")
    return WAITING_FOR_POST


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال الصورة"""
    try:
        photo = update.message.photo[-1]  # أعلى دقة
        file = await photo.get_file()
        
        # اسم فريد للصورة
        from datetime import datetime
        filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = f"{content_manager.images_dir}/{filename}"
        
        await file.download_to_drive(filepath)
        
        await update.message.reply_text(f"✅ تم حفظ الصورة: {filename}")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error receiving image: {e}")
        await update.message.reply_text(f"❌ خطأ في حفظ الصورة: {str(e)}")
        return ConversationHandler.END


async def receive_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال المنشور"""
    try:
        text = update.message.text
        
        from datetime import datetime
        filename = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = f"{content_manager.posts_dir}/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        await update.message.reply_text(f"✅ تم حفظ المنشور: {filename}")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error receiving post: {e}")
        await update.message.reply_text(f"❌ خطأ في حفظ المنشور: {str(e)}")
        return ConversationHandler.END


async def list_contents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المحتوى"""
    query = update.callback_query
    
    stats = content_manager.get_stats()
    images = content_manager.get_images()[:5]
    posts = content_manager.get_posts()[:5]
    
    text = f"📋 *محتويات المكتبة*\n\n"
    text += f"🖼️ *الصور ({stats['images']}):*\n"
    for img in images:
        text += f"  • `{img}`\n"
    
    text += f"\n📄 *المنشورات ({stats['posts']}):*\n"
    for post in posts:
        text += f"  • `{post}`\n"
    
    if stats['images'] > 5 or stats['posts'] > 5:
        text += "\n_(يوجد المزيد...)_"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def send_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال محتوى عشوائي"""
    query = update.callback_query
    
    import random
    choice = random.choice(['image', 'post'])
    
    try:
        if choice == 'image':
            path = content_manager.get_random_image()
            if path:
                with open(path, 'rb') as f:
                    await context.bot.send_photo(
                        chat_id=config.CHANNEL_ID,
                        photo=f,
                        caption="🎲 محتوى عشوائي"
                    )
        else:
            text = content_manager.get_random_post()
            if text:
                await context.bot.send_message(
                    chat_id=config.CHANNEL_ID,
                    text=text[:4096]
                )
        
        await query.edit_message_text("✅ تم إرسال محتوى عشوائي!")
    except Exception as e:
        logger.error(f"Error sending random: {e}")
        await query.edit_message_text(f"❌ خطأ: {str(e)}")


async def close_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إغلاق اللوحة"""
    query = update.callback_query
    await query.edit_message_text("✅ تم إغلاق لوحة التحكم.")
    return ConversationHandler.END


async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للوحة التحكم"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🖼️ إرسال صورة", callback_data="send_image")],
        [InlineKeyboardButton("📝 إرسال منشور", callback_data="send_post")],
        [InlineKeyboardButton("➕ إضافة صورة", callback_data="add_image")],
        [InlineKeyboardButton("✏️ إضافة منشور", callback_data="add_post")],
        [InlineKeyboardButton("📋 عرض المحتوى", callback_data="list_contents")],
        [InlineKeyboardButton("🎲 محتوى عشوائي", callback_data="random_content")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ]
    
    await query.edit_message_text(
        "🎛️ *لوحة تحكم القناة*\n\nاختر ما تريد القيام به:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية"""
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END