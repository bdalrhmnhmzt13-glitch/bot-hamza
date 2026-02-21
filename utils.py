#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دوال مساعدة عامة
"""
import os
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
import messages


class ContentManager:
    """مدير المحتوى (صور ومنشورات)"""
    
    def __init__(self, images_dir: str = "images", posts_dir: str = "posts"):
        self.images_dir = images_dir
        self.posts_dir = posts_dir
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """التأكد من وجود المجلدات"""
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
    
    def get_images(self) -> List[str]:
        """الحصول على قائمة الصور"""
        try:
            return [f for f in os.listdir(self.images_dir) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        except FileNotFoundError:
            return []
    
    def get_posts(self) -> List[str]:
        """الحصول على قائمة المنشورات"""
        try:
            return [f for f in os.listdir(self.posts_dir) 
                    if f.endswith('.txt')]
        except FileNotFoundError:
            return []
    
    def get_random_image(self) -> Optional[str]:
        """اختيار صورة عشوائية"""
        images = self.get_images()
        if not images:
            return None
        return os.path.join(self.images_dir, random.choice(images))
    
    def get_random_post(self) -> Optional[str]:
        """اختيار منشور عشوائي"""
        posts = self.get_posts()
        if not posts:
            return None
        
        post_path = os.path.join(self.posts_dir, random.choice(posts))
        try:
            with open(post_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """إحصائيات المحتوى"""
        return {
            'images': len(self.get_images()),
            'posts': len(self.get_posts())
        }


class HadithManager:
    """مدير الأحاديث"""
    
    @staticmethod
    def get_random() -> Dict[str, str]:
        """اختيار حديث عشوائي"""
        return random.choice(messages.AHADITH)
    
    @staticmethod
    def format(hadith: Dict[str, str]) -> str:
        """تنسيق الحديث للعرض"""
        return messages.HADITH_TEMPLATE.format(
            text=hadith['text'],
            source=hadith['source'],
            explanation=hadith['explanation'],
            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    @staticmethod
    def format_safe(hadith: Dict[str, str]) -> str:
        """تنسيق آمن بدون Markdown"""
        return f"""
🕌 حديث نبوي شريف

📖 {hadith['text']}

📚 المصدر: {hadith['source']}
💡 شرح: {hadith['explanation']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤲 تم النشر بواسطة بوت hamza_Root
"""


class MarkdownHelper:
    """مساعد Markdown"""
    
    ESCAPE_CHARS = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    @classmethod
    def escape(cls, text: str) -> str:
        """تجاوز رموز Markdown"""
        if not text:
            return text
        for char in cls.ESCAPE_CHARS:
            text = text.replace(char, f'\\{char}')
        return text
    
    @classmethod
    def safe_text(cls, text: str) -> str:
        """إزالة جميع الرموز الخاصة"""
        if not text:
            return ""
        for char in cls.ESCAPE_CHARS:
            text = text.replace(char, '')
        return text.strip()


# نسخ عامة
content_manager = ContentManager()
hadith_manager = HadithManager()