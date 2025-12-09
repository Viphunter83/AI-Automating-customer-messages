"""
Telegram Bot Handlers
Command handlers and message handlers for Telegram bot
"""
import logging
from typing import Dict

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "👋 Привет! Я бот для тестирования системы автоматизации клиентских сообщений.\n\n"
        "Просто отправь мне сообщение, и я обработаю его с помощью AI.\n\n"
        "Команды:\n"
        "/help - показать справку\n"
        "/start - начать заново"
    )
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {update.effective_user.id} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = (
        "📖 Справка по использованию бота:\n\n"
        "Отправь любое текстовое сообщение, и система:\n"
        "1. Проанализирует его с помощью AI\n"
        "2. Классифицирует по сценарию\n"
        "3. Отправит автоматический ответ\n\n"
        "Если сообщение требует внимания оператора, оно будет эскалировано.\n\n"
        "Команды:\n"
        "/start - начать\n"
        "/help - эта справка"
    )
    
    await update.message.reply_text(help_message)
    logger.info(f"User {update.effective_user.id} requested help")










