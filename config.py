#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sys
from dataclasses import dataclass
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class Config:
    TOKEN: str = ""
    CHANNEL_ID: int = 0
    ADMIN_IDS: List[int] = None
    LOG_LEVEL: str = "INFO"
    IMAGES_DIR: str = "images"
    POSTS_DIR: str = "posts"
    HADITH_INTERVAL: int = 3600
    FIRST_DELAY: int = 5
    
    @classmethod
    def from_env(cls):
        token = os.getenv('TOKEN', '')
        channel_id = int(os.getenv('CHANNEL_ID', '0') or 0)
        
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().lstrip('-').isdigit()]
        
        return cls(
            TOKEN=token,
            CHANNEL_ID=channel_id,
            ADMIN_IDS=admin_ids,
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
            IMAGES_DIR=os.getenv('IMAGES_DIR', 'images'),
            POSTS_DIR=os.getenv('POSTS_DIR', 'posts'),
            HADITH_INTERVAL=int(os.getenv('HADITH_INTERVAL', '3600')),
            FIRST_DELAY=int(os.getenv('FIRST_DELAY', '5'))
        )
    
    def validate(self):
        if not self.TOKEN:
            raise ValueError("TOKEN مطلوب")
        if not self.CHANNEL_ID:
            raise ValueError("CHANNEL_ID مطلوب")
        return True


def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


config = Config.from_env()
logger = setup_logging(config.LOG_LEVEL)
