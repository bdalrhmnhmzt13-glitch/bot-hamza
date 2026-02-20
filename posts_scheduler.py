#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import random
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from media_manager import MediaManager

logger = logging.getLogger(__name__)

class PostsScheduler:
    """جدولة المنشورات التلقائية"""
    
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.scheduler = AsyncIOScheduler()
        self.media_manager = MediaManager()
        self.setup_schedule()
    
    def setup_schedule(self):
        """إعداد جدول النشر"""
        
        # نشر كل 3 ساعات
        self.scheduler.add_job(
            self.send_random_post,
            trigger='interval',
            hours=3,
            id='every_3_hours',
            name='نشر كل 3 ساعات'
        )
        
        # نشر في أوقات محددة (مثلاً الفجر والمغرب)
        self.scheduler.add_job(
            self.send_islamic_post,
            trigger=CronTrigger(hour=4, minute=30),  # وقت الفجر
            id='fajr_post',
            name='نشر وقت الفجر'
        )
        
        self.scheduler.add_job(
            self.send_islamic_post,
            trigger=CronTrigger(hour=17, minute=45),  # وقت المغرب
            id='maghrib_post',
            name='نشر وقت المغرب'
        )
        
        # نشر صباحي
        self.scheduler.add_job(
            self.send_morning_post,
            trigger=CronTrigger(hour=8, minute=0),
            id='morning_post',
            name='نشر صباحي'
        )
        
        # نشر مسائي
        self.scheduler.add_job(
            self.send_evening_post,
            trigger=CronTrigger(hour=20, minute=0),
            id='evening_post',
            name='نشر مسائي'
        )
        
        logger.info("✅ تم إعداد جدولة المنشورات")
    
    async def send_random_post(self):
        """إرسال منشور عشوائي"""
        try:
            content = self.media_manager.get_random_content()
            
            if content['type'] == 'image_text':
                with open(content['image'], 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=photo,
                        caption=content['text'],
                        parse_mode='Markdown'
                    )
            elif content['type'] == 'image_only':
                with open(content['image'], 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=photo
                    )
            else:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=content['text'],
                    parse_mode='Markdown'
                )
            
            logger.info("✅ تم إرسال منشور عشوائي للقناة")
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال المنشور العشوائي: {e}")
    
    async def send_islamic_post(self):
        """إرسال منشور إسلامي (حديث أو آية)"""
        try:
            # يمكنك تخصيص هذا أكثر
            post = self.media_manager.get_random_post()
            if post:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=f"🕌 *ذكرى الإسلام*\n\n{post}",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال المنشور الإسلامي: {e}")
    
    async def send_morning_post(self):
        """نشر صباحي"""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text="🌅 *صباح الخير*\n\nاللهم بك أصبحنا وبك أمسينا، وبك نحيا وبك نموت وإليك النشور.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ خطأ في النشر الصباحي: {e}")
    
    async def send_evening_post(self):
        """نشر مسائي"""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text="🌇 *مساء الخير*\n\nاللهم بك أمسينا وبك أصبحنا، وبك نحيا وبك نموت وإليك المصير.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ خطأ في النشر المسائي: {e}")
    
    def start(self):
        """بدء الجدولة"""
        self.scheduler.start()
        logger.info("🚀 تم بدء جدولة المنشورات")
    
    def stop(self):
        """إيقاف الجدولة"""
        self.scheduler.shutdown()
        logger.info("🛑 تم إيقاف جدولة المنشورات")
    
    def add_custom_job(self, func, trigger, **kwargs):
        """إضافة مهمة مخصصة"""
        self.scheduler.add_job(func, trigger, **kwargs)