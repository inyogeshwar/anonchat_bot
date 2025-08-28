
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the bot"""

    # Bot token from BotFather
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

    # Bot settings
    MAX_WAITING_TIME = 300  # Maximum time to wait for a partner (seconds)
    ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Admin user ID for monitoring

    # Feature flags
    ENABLE_MEDIA_SHARING = True
    ENABLE_PROFANITY_FILTER = False
    MAX_MESSAGE_LENGTH = 4000

    # Database settings (for future expansion)
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            raise ValueError("Bot token not configured! Please set BOT_TOKEN in .env file")

        return True
