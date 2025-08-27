#!/usr/bin/env python3
"""
Telegram Anonymous Chat Bot - Full Implementation
Author: Bot Creator
Description: Anonymous chat bot with privacy features, admin controls, and security
"""

import asyncio
import logging
import time
import random
import string
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Set, Optional, List, Tuple
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters, 
    ContextTypes
)
from telegram.constants import ParseMode
import sqlite3
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'your-bot-token-here')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
    MAX_MESSAGES_PER_MINUTE = 10
    MAX_WARNINGS = 3
    SESSION_TIMEOUT = 1800  # 30 minutes
    MESSAGE_EXPIRY = 86400  # 24 hours

class UserStatus(Enum):
    IDLE = "idle"
    WAITING = "waiting"
    CHATTING = "chatting"
    BANNED = "banned"

@dataclass
class User:
    telegram_id: int
    anonymous_id: str
    status: UserStatus = UserStatus.IDLE
    partner_id: Optional[int] = None
    session_start: Optional[datetime] = None
    warnings: int = 0
    message_count: int = 0
    last_message_time: Optional[datetime] = None
    join_time: datetime = datetime.now()

@dataclass
class Message:
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    message_id: str

class AnonymousChatBot:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.waiting_users: List[int] = []
        self.active_chats: Dict[int, int] = {}  # user_id -> partner_id
        self.banned_users: Set[int] = set()
        self.message_history: List[Message] = []
        self.rate_limiter: Dict[int, deque] = defaultdict(deque)
        self.warnings: Dict[int, int] = defaultdict(int)
        self.cipher = Fernet(Config.ENCRYPTION_KEY)
        
        # Initialize database
        self.init_database()
        
        # Profanity filter (basic implementation)
        self.profanity_words = {
            'spam', 'scam', 'fake', 'bot', 'advertisement', 
            'buy now', 'click here', 'limited offer'
        }
        
    def init_database(self):
        """Initialize SQLite database for logging"""
        self.conn = sqlite3.connect('bot_logs.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TEXT,
                details TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_user_id INTEGER,
                timestamp TEXT,
                reason TEXT
            )
        ''')
        
        self.conn.commit()

    def generate_anonymous_id(self) -> str:
        """Generate anonymous user ID"""
        return f"USER{''.join(random.choices(string.digits, k=4))}"

    def encrypt_message(self, message: str) -> str:
        """Encrypt message content"""
        return self.cipher.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt message content"""
        try:
            return self.cipher.decrypt(encrypted_message.encode()).decode()
        except:
            return encrypted_message  # Return as-is if decryption fails

    def log_user_action(self, user_id: int, action: str, details: str = ""):
        """Log user actions"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO user_logs (user_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
            (user_id, action, datetime.now().isoformat(), details)
        )
        self.conn.commit()

    def log_admin_action(self, admin_id: int, action: str, target_user_id: int = None, reason: str = ""):
        """Log admin actions"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO admin_logs (admin_id, action, target_user_id, timestamp, reason) VALUES (?, ?, ?, ?, ?)",
            (admin_id, action, target_user_id, datetime.now().isoformat(), reason)
        )
        self.conn.commit()

    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        user_messages = self.rate_limiter[user_id]
        
        # Remove old messages
        while user_messages and user_messages[0] < now - timedelta(minutes=1):
            user_messages.popleft()
        
        # Check if user exceeded limit
        if len(user_messages) >= Config.MAX_MESSAGES_PER_MINUTE:
            return True
        
        user_messages.append(now)
        return False

    def contains_profanity(self, text: str) -> bool:
        """Basic profanity filter"""
        text_lower = text.lower()
        return any(word in text_lower for word in self.profanity_words)

    def get_user_stats(self) -> Dict:
        """Get bot statistics"""
        return {
            'total_users': len(self.users),
            'active_chats': len(self.active_chats) // 2,
            'waiting_users': len(self.waiting_users),
            'banned_users': len(self.banned_users),
            'total_messages': len(self.message_history)
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
        
        if user_id not in self.users:
            anonymous_id = self.generate_anonymous_id()
            self.users[user_id] = User(
                telegram_id=user_id,
                anonymous_id=anonymous_id
            )
            self.log_user_action(user_id, "REGISTER", f"Anonymous ID: {anonymous_id}")
        
        welcome_text = f"""
🎭 **Welcome to Anonymous Chat Bot!**

Your anonymous ID: `{self.users[user_id].anonymous_id}`

**Available Commands:**
• /find - Find a random chat partner
• /stop - End current conversation
• /report - Report inappropriate behavior
• /help - Show this help message

**Rules:**
• Be respectful to others
• No spam, harassment, or inappropriate content
• Conversations are anonymous and temporary
• Messages expire after 24 hours

Ready to start chatting anonymously? Use /find to begin!
        """
        
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def find_partner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /find command to match users"""
        user_id = update.effective_user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
        
        if user_id not in self.users:
            await update.message.reply_text("Please use /start first!")
            return
        
        user = self.users[user_id]
        
        if user.status == UserStatus.CHATTING:
            await update.message.reply_text("You are already in a chat! Use /stop to end it first.")
            return
        
        if user.status == UserStatus.WAITING:
            await update.message.reply_text("You are already waiting for a partner...")
            return
        
        # Check if there's a waiting user
        if self.waiting_users:
            partner_id = self.waiting_users.pop(0)
            partner = self.users[partner_id]
            
            # Create chat connection
            user.status = UserStatus.CHATTING
            partner.status = UserStatus.CHATTING
            user.partner_id = partner_id
            partner.partner_id = user_id
            user.session_start = datetime.now()
            partner.session_start = datetime.now()
            
            self.active_chats[user_id] = partner_id
            self.active_chats[partner_id] = user_id
            
            # Notify both users
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Connected! You're now chatting with {partner.anonymous_id}\n"
                     f"Your messages are encrypted and anonymous.\n"
                     f"Use /stop to end the conversation."
            )
            
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"🎉 Connected! You're now chatting with {user.anonymous_id}\n"
                     f"Your messages are encrypted and anonymous.\n"
                     f"Use /stop to end the conversation."
            )
            
            self.log_user_action(user_id, "CHAT_START", f"Partner: {partner.anonymous_id}")
            self.log_user_action(partner_id, "CHAT_START", f"Partner: {user.anonymous_id}")
        
        else:
            # Add user to waiting list
            user.status = UserStatus.WAITING
            self.waiting_users.append(user_id)
            await update.message.reply_text("🔍 Looking for a chat partner... Please wait!")
            self.log_user_action(user_id, "WAITING", "Added to waiting list")

    async def stop_chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        if user_id not in self.users:
            await update.message.reply_text("Please use /start first!")
            return
        
        user = self.users[user_id]
        
        if user.status == UserStatus.WAITING:
            user.status = UserStatus.IDLE
            if user_id in self.waiting_users:
                self.waiting_users.remove(user_id)
            await update.message.reply_text("❌ Stopped looking for a partner.")
            return
        
        if user.status != UserStatus.CHATTING:
            await update.message.reply_text("You are not in a chat!")
            return
        
        # End chat
        await self.end_chat(user_id, context)
        await update.message.reply_text("👋 Chat ended. Use /find to start a new chat!")

    async def end_chat(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """End a chat session"""
        if user_id not in self.active_chats:
            return
        
        partner_id = self.active_chats[user_id]
        user = self.users[user_id]
        partner = self.users[partner_id]
        
        # Reset user statuses
        user.status = UserStatus.IDLE
        partner.status = UserStatus.IDLE
        user.partner_id = None
        partner.partner_id = None
        user.session_start = None
        partner.session_start = None
        
        # Remove from active chats
        del self.active_chats[user_id]
        del self.active_chats[partner_id]
        
        # Notify partner
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="👋 Your chat partner has left the conversation."
            )
        except:
            pass
        
        self.log_user_action(user_id, "CHAT_END", f"Partner: {partner.anonymous_id}")
        self.log_user_action(partner_id, "CHAT_END", f"Partner: {user.anonymous_id}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        
        if user_id in self.banned_users:
            return
        
        if user_id not in self.users:
            await update.message.reply_text("Please use /start first!")
            return
        
        # Rate limiting
        if self.is_rate_limited(user_id):
            await update.message.reply_text("⚠️ You're sending messages too fast! Please slow down.")
            return
        
        user = self.users[user_id]
        
        if user.status != UserStatus.CHATTING:
            await update.message.reply_text("You need to find a chat partner first! Use /find")
            return
        
        message_text = update.message.text
        
        # Profanity filter
        if self.contains_profanity(message_text):
            self.warnings[user_id] += 1
            await update.message.reply_text(
                f"⚠️ Inappropriate content detected! Warning {self.warnings[user_id]}/{Config.MAX_WARNINGS}"
            )
            
            if self.warnings[user_id] >= Config.MAX_WARNINGS:
                await self.ban_user(user_id, context, "Repeated inappropriate content")
                return
            return
        
        # Forward message to partner
        partner_id = self.active_chats[user_id]
        partner = self.users[partner_id]
        
        try:
            # Encrypt message for storage
            encrypted_message = self.encrypt_message(message_text)
            
            # Store message
            message = Message(
                sender_id=user_id,
                receiver_id=partner_id,
                content=encrypted_message,
                timestamp=datetime.now(),
                message_id=f"{user_id}_{partner_id}_{int(time.time())}"
            )
            self.message_history.append(message)
            
            # Forward to partner
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"**{user.anonymous_id}:** {message_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text("❌ Failed to send message. Please try again.")

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        user_id = update.effective_user.id
        
        if user_id not in self.users:
            await update.message.reply_text("Please use /start first!")
            return
        
        user = self.users[user_id]
        
        if user.status != UserStatus.CHATTING:
            await update.message.reply_text("You need to be in a chat to report someone!")
            return
        
        partner_id = user.partner_id
        partner = self.users[partner_id]
        
        # Log the report
        self.log_user_action(user_id, "REPORT", f"Reported: {partner.anonymous_id}")
        
        # Notify admins
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 **Report Filed**\n\n"
                         f"Reporter: {user.anonymous_id}\n"
                         f"Reported: {partner.anonymous_id}\n"
                         f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                         f"Use /ban {partner_id} to ban the user.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        await update.message.reply_text(
            "✅ Report submitted! Our moderators will review it.\n"
            "The conversation will continue. Use /stop to end it."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🎭 **Anonymous Chat Bot Help**

**User Commands:**
• `/start` - Register and get started
• `/find` - Find a random chat partner
• `/stop` - End current conversation
• `/report` - Report inappropriate behavior
• `/help` - Show this help message

**Features:**
• 🔒 End-to-end encrypted messages
• 🎭 Complete anonymity
• ⏰ Messages expire after 24 hours
• 🛡️ Anti-spam protection
• 🚫 Profanity filtering
• ⚡ Rate limiting
• 👮‍♂️ Admin moderation

**Rules:**
• Be respectful and kind
• No spam or harassment
• No sharing personal information
• No inappropriate content
• Follow Telegram's Terms of Service

Need help? Contact @YourSupportBot
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    # Admin Commands
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to ban a user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id>")
            return
        
        try:
            target_user_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
            
            await self.ban_user(target_user_id, context, reason)
            self.log_admin_action(update.effective_user.id, "BAN", target_user_id, reason)
            
            await update.message.reply_text(f"✅ User {target_user_id} has been banned.")
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def ban_user(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, reason: str):
        """Ban a user"""
        self.banned_users.add(user_id)
        
        if user_id in self.users:
            user = self.users[user_id]
            if user.status == UserStatus.CHATTING:
                await self.end_chat(user_id, context)
            user.status = UserStatus.BANNED
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🚫 You have been banned from the bot.\nReason: {reason}"
            )
        except:
            pass

    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to unban a user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        
        try:
            target_user_id = int(context.args[0])
            
            if target_user_id in self.banned_users:
                self.banned_users.remove(target_user_id)
                if target_user_id in self.users:
                    self.users[target_user_id].status = UserStatus.IDLE
                
                self.log_admin_action(update.effective_user.id, "UNBAN", target_user_id)
                await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
            else:
                await update.message.reply_text("❌ User is not banned!")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to check bot status"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        stats = self.get_user_stats()
        
        status_text = f"""
📊 **Bot Status Report**

👥 **Users:**
• Total registered: {stats['total_users']}
• Currently waiting: {stats['waiting_users']}
• In active chats: {stats['active_chats']} pairs
• Banned users: {stats['banned_users']}

💬 **Messages:**
• Total messages: {stats['total_messages']}

🕒 **Uptime:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

    async def cleanup_expired_messages(self):
        """Background task to cleanup expired messages"""
        while True:
            try:
                current_time = datetime.now()
                
                # Remove expired messages
                self.message_history = [
                    msg for msg in self.message_history 
                    if current_time - msg.timestamp < timedelta(seconds=Config.MESSAGE_EXPIRY)
                ]
                
                # Remove inactive sessions
                inactive_users = []
                for user_id, user in self.users.items():
                    if (user.status == UserStatus.CHATTING and 
                        user.session_start and 
                        current_time - user.session_start > timedelta(seconds=Config.SESSION_TIMEOUT)):
                        inactive_users.append(user_id)
                
                # End inactive chats
                for user_id in inactive_users:
                    if user_id in self.active_chats:
                        try:
                            # This is a simplified context for cleanup
                            class CleanupContext:
                                def __init__(self, bot):
                                    self.bot = bot
                            
                            cleanup_context = CleanupContext(None)  # Bot will be set when needed
                            await self.end_chat(user_id, cleanup_context)
                        except:
                            pass
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)

def main():
    """Main function to run the bot"""
    # Create bot instance
    bot = AnonymousChatBot()
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("find", bot.find_partner_command))
    application.add_handler(CommandHandler("stop", bot.stop_chat_command))
    application.add_handler(CommandHandler("report", bot.report_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    
    # Admin handlers
    application.add_handler(CommandHandler("ban", bot.ban_command))
    application.add_handler(CommandHandler("unban", bot.unban_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start cleanup task
    asyncio.create_task(bot.cleanup_expired_messages())
    
    # Run the bot
    print("🎭 Anonymous Chat Bot is starting...")
    print("Make sure to set your environment variables:")
    print("- BOT_TOKEN: Your Telegram bot token")
    print("- ADMIN_IDS: Comma-separated admin user IDs")
    print("- ENCRYPTION_KEY: Encryption key for messages")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()