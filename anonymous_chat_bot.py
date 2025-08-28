
import telebot
import random
import threading
import time
from typing import Dict, Set, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnonymousChatBot:
    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token)
        self.waiting_users: Set[int] = set()  # Users waiting to be matched
        self.active_chats: Dict[int, int] = {}  # user_id -> partner_id mapping
        self.user_pseudonyms: Dict[int, str] = {}  # user_id -> pseudonym
        self.pseudonym_counter = 1
        self.lock = threading.Lock()

        # List of available pseudonyms
        self.pseudonym_list = [
            "Shadow", "Phoenix", "Ghost", "Mystic", "Phantom", "Echo", "Storm",
            "Raven", "Wolf", "Tiger", "Dragon", "Eagle", "Fox", "Lion", "Bear",
            "Falcon", "Hawk", "Panther", "Viper", "Cobra", "Shark", "Knight",
            "Wizard", "Warrior", "Hunter", "Seeker", "Wanderer", "Dreamer"
        ]

        # Setup handlers
        self.setup_handlers()

    def generate_pseudonym(self) -> str:
        """Generate a unique pseudonym for a user"""
        if len(self.pseudonym_list) > 0:
            return random.choice(self.pseudonym_list) + str(random.randint(1, 999))
        return f"Anonymous{self.pseudonym_counter}"

    def setup_handlers(self):
        """Setup message handlers"""

        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            user_id = message.chat.id
            welcome_text = """
🎭 **Welcome to Anonymous Chat Bot!**

Connect with strangers anonymously and have interesting conversations!

**Available Commands:**
/find - Find a random chat partner
/next - Skip current chat and find new partner
/stop - Stop current chat
/help - Show this help message

**How it works:**
1. Use /find to search for a chat partner
2. Once connected, all messages will be forwarded anonymously
3. Use /next to find a different partner
4. Use /stop to end the current chat

Ready to start chatting anonymously? 🚀
            """
            self.bot.send_message(user_id, welcome_text, parse_mode='Markdown')

        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            start_command(message)

        @self.bot.message_handler(commands=['find'])
        def find_partner(message):
            user_id = message.chat.id

            with self.lock:
                # Check if user is already in a chat
                if user_id in self.active_chats:
                    self.bot.send_message(user_id, "❌ You're already in a chat! Use /next to find a new partner or /stop to end current chat.")
                    return

                # Check if user is already waiting
                if user_id in self.waiting_users:
                    self.bot.send_message(user_id, "⏳ You're already searching for a partner. Please wait...")
                    return

                # Try to find a partner from waiting users
                if self.waiting_users:
                    partner_id = self.waiting_users.pop()

                    # Create chat connection
                    self.active_chats[user_id] = partner_id
                    self.active_chats[partner_id] = user_id

                    # Generate pseudonyms
                    user_pseudonym = self.generate_pseudonym()
                    partner_pseudonym = self.generate_pseudonym()

                    self.user_pseudonyms[user_id] = user_pseudonym
                    self.user_pseudonyms[partner_id] = partner_pseudonym

                    # Notify both users
                    self.bot.send_message(user_id, f"✅ **Connected!** You are now chatting as **{user_pseudonym}**\n\nYour partner is **{partner_pseudonym}**\n\nStart your conversation! Use /next for new partner or /stop to end chat.", parse_mode='Markdown')
                    self.bot.send_message(partner_id, f"✅ **Connected!** You are now chatting as **{partner_pseudonym}**\n\nYour partner is **{user_pseudonym}**\n\nStart your conversation! Use /next for new partner or /stop to end chat.", parse_mode='Markdown')

                    logger.info(f"Connected users {user_id} ({user_pseudonym}) and {partner_id} ({partner_pseudonym})")

                else:
                    # Add to waiting list
                    self.waiting_users.add(user_id)
                    self.bot.send_message(user_id, "🔍 **Searching for a chat partner...**\n\nPlease wait while we find someone for you to chat with!", parse_mode='Markdown')
                    logger.info(f"User {user_id} added to waiting list")

        @self.bot.message_handler(commands=['next'])
        def next_partner(message):
            user_id = message.chat.id

            with self.lock:
                if user_id not in self.active_chats:
                    self.bot.send_message(user_id, "❌ You're not in any chat! Use /find to start chatting.")
                    return

                # Get partner and disconnect
                partner_id = self.active_chats[user_id]

                # Notify both users
                self.bot.send_message(user_id, "👋 **Chat ended!** Your partner left. Use /find to start a new chat.")
                self.bot.send_message(partner_id, "👋 **Chat ended!** Your partner left. Use /find to start a new chat.")

                # Clean up
                self.cleanup_chat(user_id, partner_id)

                logger.info(f"User {user_id} skipped chat with {partner_id}")

            # Automatically find new partner
            find_partner(message)

        @self.bot.message_handler(commands=['stop'])
        def stop_chat(message):
            user_id = message.chat.id

            with self.lock:
                # Remove from waiting list if present
                if user_id in self.waiting_users:
                    self.waiting_users.remove(user_id)
                    self.bot.send_message(user_id, "❌ **Search cancelled!** Use /find when you want to chat again.")
                    return

                # End active chat if present
                if user_id in self.active_chats:
                    partner_id = self.active_chats[user_id]

                    # Notify both users
                    self.bot.send_message(user_id, "👋 **Chat ended!** Use /find to start a new chat.")
                    self.bot.send_message(partner_id, "👋 **Chat ended!** Your partner left. Use /find to start a new chat.")

                    # Clean up
                    self.cleanup_chat(user_id, partner_id)

                    logger.info(f"User {user_id} stopped chat with {partner_id}")
                else:
                    self.bot.send_message(user_id, "❌ You're not in any chat or search queue!")

        @self.bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'audio', 'document', 'voice', 'sticker'])
        def handle_message(message):
            user_id = message.chat.id

            with self.lock:
                # Check if user is in active chat
                if user_id not in self.active_chats:
                    self.bot.send_message(user_id, "❌ You're not connected to anyone! Use /find to start chatting.")
                    return

                partner_id = self.active_chats[user_id]
                user_pseudonym = self.user_pseudonyms.get(user_id, "Anonymous")

            # Forward message to partner with pseudonym
            try:
                if message.content_type == 'text':
                    formatted_message = f"**{user_pseudonym}:** {message.text}"
                    self.bot.send_message(partner_id, formatted_message, parse_mode='Markdown')

                elif message.content_type == 'photo':
                    caption = f"**{user_pseudonym}** sent a photo"
                    if message.caption:
                        caption += f": {message.caption}"
                    self.bot.send_photo(partner_id, message.photo[-1].file_id, caption=caption, parse_mode='Markdown')

                elif message.content_type == 'video':
                    caption = f"**{user_pseudonym}** sent a video"
                    if message.caption:
                        caption += f": {message.caption}"
                    self.bot.send_video(partner_id, message.video.file_id, caption=caption, parse_mode='Markdown')

                elif message.content_type == 'audio':
                    caption = f"**{user_pseudonym}** sent an audio"
                    self.bot.send_audio(partner_id, message.audio.file_id, caption=caption, parse_mode='Markdown')

                elif message.content_type == 'voice':
                    caption = f"**{user_pseudonym}** sent a voice message"
                    self.bot.send_voice(partner_id, message.voice.file_id, caption=caption, parse_mode='Markdown')

                elif message.content_type == 'document':
                    caption = f"**{user_pseudonym}** sent a document"
                    if message.caption:
                        caption += f": {message.caption}"
                    self.bot.send_document(partner_id, message.document.file_id, caption=caption, parse_mode='Markdown')

                elif message.content_type == 'sticker':
                    self.bot.send_message(partner_id, f"**{user_pseudonym}** sent a sticker", parse_mode='Markdown')
                    self.bot.send_sticker(partner_id, message.sticker.file_id)

            except Exception as e:
                logger.error(f"Error forwarding message: {e}")
                self.bot.send_message(user_id, "❌ Failed to send message. Your partner might have left the chat.")

    def cleanup_chat(self, user_id: int, partner_id: int):
        """Clean up chat session data"""
        # Remove from active chats
        self.active_chats.pop(user_id, None)
        self.active_chats.pop(partner_id, None)

        # Remove pseudonyms
        self.user_pseudonyms.pop(user_id, None)
        self.user_pseudonyms.pop(partner_id, None)

    def start_polling(self):
        """Start the bot with error handling"""
        logger.info("Starting Anonymous Chat Bot...")
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)
            self.start_polling()

# Main execution
if __name__ == "__main__":
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token from BotFather
    BOT_TOKEN = "YOUR_BOT_TOKEN"

    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ Please replace 'YOUR_BOT_TOKEN' with your actual bot token!")
        print("Get your token from @BotFather on Telegram")
        exit(1)

    # Create and start the bot
    anonymous_bot = AnonymousChatBot(BOT_TOKEN)
    anonymous_bot.start_polling()
