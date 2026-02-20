#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MediaManager:
    """إدارة الصور والوسائط للقناة"""
    
    def __init__(self):
        # المسارات
        self.images_path = Path("images")
        self.posts_path = Path("posts")
        
        # إنشاء المجلدات إذا لم تكن موجودة
        self.images_path.mkdir(exist_ok=True)
        self.posts_path.mkdir(exist_ok=True)
        
        # أنواع الصور المدعومة
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
    def get_random_image(self):
        """الحصول على صورة عشوائية من مجلد images"""
        try:
            # جمع كل الصور في المجلد
            images = []
            for ext in self.image_extensions:
                images.extend(self.images_path.glob(f"*{ext}"))
                images.extend(self.images_path.glob(f"*{ext.upper()}"))
            
            if not images:
                logger.warning("لا توجد صور في مجلد images")
                return None
                
            return random.choice(images)
        except Exception as e:
            logger.error(f"خطأ في الحصول على صورة: {e}")
            return None
    
    def get_random_post(self):
        """الحصول على منشور نصي عشوائي"""
        try:
            posts = list(self.posts_path.glob("*.txt"))
            if not posts:
                logger.warning("لا توجد منشورات في مجلد posts")
                return None
                
            post_file = random.choice(posts)
            with open(post_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"خطأ في قراءة المنشور: {e}")
            return None
    
    def get_random_content(self):
        """اختيار عشوائي بين صورة + نص أو نص فقط"""
        content_type = random.choice(['image_text', 'text_only', 'image_only'])
        
        result = {'type': content_type}
        
        if content_type in ['image_text', 'image_only']:
            image_path = self.get_random_image()
            if image_path:
                result['image'] = str(image_path)
            else:
                result['type'] = 'text_only' if content_type == 'image_text' else 'text_only'
        
        if content_type in ['image_text', 'text_only']:
            post = self.get_random_post()
            if post:
                result['text'] = post
            elif 'image' in result:
                result['type'] = 'image_only'
            else:
                result['type'] = 'text_only'
                result['text'] = "❌ لا توجد منشورات متاحة"
        
        return result
    
    def add_image(self, image_path, custom_name=None):
        """إضافة صورة إلى المجلد"""
        try:
            if not os.path.exists(image_path):
                return False, "الملف غير موجود"
            
            # تحديد الاسم الجديد
            if custom_name:
                new_name = custom_name
            else:
                # استخدام الوقت كاسم
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = Path(image_path).suffix
                new_name = f"image_{timestamp}{ext}"
            
            # نسخ الصورة
            import shutil
            dest = self.images_path / new_name
            shutil.copy2(image_path, dest)
            
            return True, f"تم إضافة الصورة: {new_name}"
        except Exception as e:
            return False, str(e)
    
    def add_post(self, text, title=None):
        """إضافة منشور نصي"""
        try:
            if title:
                filename = f"{title}.txt"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"post_{timestamp}.txt"
            
            filepath = self.posts_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True, f"تم إضافة المنشور: {filename}"
        except Exception as e:
            return False, str(e)
    
    def list_contents(self):
        """عرض محتويات المجلدات"""
        images = []
        for ext in self.image_extensions:
            images.extend(self.images_path.glob(f"*{ext}"))
        
        posts = list(self.posts_path.glob("*.txt"))
        
        return {
            'images': [img.name for img in images],
            'posts': [post.name for post in posts],
            'images_count': len(images),
            'posts_count': len(posts)
        }