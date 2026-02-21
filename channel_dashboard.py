#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from media_manager import MediaManager

logger = logging.getLogger(__name__)

# حالات المحادثة
SELECTING_ACTION, WAITING_FOR_IMAGE, WAITING_FOR_POST = range(3)


class ChannelDashboard:
    """لوحة تحكم القناة"""

    def __init__(self, bot_app, channel_id, admin_ids=None):
        self.app = bot_app
        self.channel_id = channel_id
        self.admin_ids = admin_ids or []
        self.media_manager = MediaManager()
        self.setup_handlers()

    def setup_handlers(self):
        """إضافة معالجات الأوامر"""

        self.app.add_handler(CommandHandler("dashboard", self.dashboard_command))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))

        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_image_start, pattern="^add_image$")],
            states={
                WAITING_FOR_IMAGE: [
                    MessageHandler(filters.PHOTO, self.receive_image)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(conv_handler)

        conv_handler2 = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_post_start, pattern="^add_post$")],
            states={
                WAITING_FOR_POST: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_post)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(conv_handler2)

    async def is_admin(self, user_id):
        if not self.admin_ids:
            return True
        return user_id in self.admin_ids

    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ عذراً، هذه اللوحة للمشرفين فقط.")
            return

        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات القناة", callback_data="stats")],
            [InlineKeyboardButton("🖼️ إرسال صورة للقناة", callback_data="send_image")],
            [InlineKeyboardButton("📝 إرسال منشور للقناة", callback_data="send_post")],
            [InlineKeyboardButton("➕ إضافة صورة للمكتبة", callback_data="add_image")],
            [InlineKeyboardButton("✏️ إضافة منشور للمكتبة", callback_data="add_post")],
            [InlineKeyboardButton("📋 عرض المحتويات", callback_data="list_contents")],
            [InlineKeyboardButton("🎲 إرسال محتوى عشوائي", callback_data="random_content")],
            [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
        ]

        await update.message.reply_text(
            "🎛️ *لوحة تحكم القناة*\n\nاختر ما تريد القيام به:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        if not await self.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية.")
            return

        actions = {
            "stats": self.show_stats,
            "send_image": self.send_image_to_channel,
            "send_post": self.send_post_to_channel,
            "add_image": self.add_image_start,
            "add_post": self.add_post_start,
            "list_contents": self.list_contents,
            "random_content": self.send_random_content,
            "close": lambda *_: query.edit_message_text("✅ تم إغلاق لوحة التحكم.")
        }

        if query.data in actions:
            await actions[query.data](update, context)

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        try:
            chat = await context.bot.get_chat(self.channel_id)
            members_count = await context.bot.get_chat_member_count(self.channel_id)

            stats_text = f"""
📊 *إحصائيات القناة*

📌 *الاسم:* {chat.title}
🆔 *المعرف:* `{chat.id}`
👥 *عدد الأعضاء:* {members_count}
📝 *الوصف:* {chat.description or 'لا يوجد'}

🖼️ *عدد الصور:* {self.media_manager.list_contents()['images_count']}
📄 *عدد المنشورات:* {self.media_manager.list_contents()['posts_count']}
"""

            await query.edit_message_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]),
                parse_mode='Markdown'
            )

        except Exception as e:
            await query.edit_message_text(f"❌ خطأ: {e}")

    async def send_image_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        image_path = self.media_manager.get_random_image()
        if not image_path:
            await query.edit_message_text("❌ لا توجد صور.")
            return

        try:
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=self.channel_id,
                    photo=photo,
                    caption="🖼️ صورة من المكتبة",
                    parse_mode='Markdown'
                )

            await query.edit_message_text("✅ تم إرسال الصورة!")

        except Exception as e:
            await query.edit_message_text(f"❌ خطأ: {e}")

    async def send_post_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        post = self.media_manager.get_random_post()
        if not post:
            await query.edit_message_text("❌ لا توجد منشورات.")
            return

        try:
            await context.bot.send_message(
                chat_id=self.channel_id,
                text=post,
                parse_mode='Markdown'
            )

            await query.edit_message_text("✅ تم إرسال المنشور!")

        except Exception as e:
            await query.edit_message_text(f"❌ خطأ: {e}")

    async def add_image_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.edit_message_text("🖼️ أرسل الصورة الآن.\nأو أرسل /cancel للإلغاء.")
        return WAITING_FOR_IMAGE

    async def receive_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.jpg"
        filepath = f"images/{filename}"

        await file.download_to_drive(filepath)

        await update.message.reply_text(f"✅ تم حفظ الصورة!\nالاسم: {filename}")
        return ConversationHandler.END

    async def add_post_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.edit_message_text("📝 أرسل النص الآن.\nأو أرسل /cancel للإلغاء.")
        return WAITING_FOR_POST

    async def receive_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"post_{timestamp}.txt"
        filepath = f"posts/{filename}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        await update.message.reply_text(f"✅ تم حفظ المنشور!\nالاسم: {filename}")
        return ConversationHandler.END

    async def list_contents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        contents = self.media_manager.list_contents()

        text = "📋 *محتويات المكتبة*\n\n"
        text += f"🖼️ الصور: {contents['images_count']}\n"
        for img in contents['images'][:10]:
            text += f"  • {img}\n"

        text += f"\n📄 المنشورات: {contents['posts_count']}\n"
        for post in contents['posts'][:10]:
            text += f"  • {post}\n"

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]),
            parse_mode='Markdown'
        )

    async def send_random_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        content = self.media_manager.get_random_content()

        try:
            if content['type'] == 'image_text':
                with open(content['image'], 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=photo,
                        caption=content['text'],
                        parse_mode='Markdown'
                    )

            elif content['type'] == 'image_only':
                with open(content['image'], 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=photo
                    )

            else:
                await context.bot.send_message(
                    chat_id=self.channel_id,
                    text=content['text'],
                    parse_mode='Markdown'
                )

            await query.edit_message_text("✅ تم إرسال محتوى عشوائي!")

        except Exception as e:
            await query.edit_message_text(f"❌ خطأ: {e}")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ تم الإلغاء.")
        return ConversationHandler.END
