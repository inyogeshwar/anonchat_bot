# Telegram Anonymous Chat Bot 🎭

A Python-based Telegram bot that connects random users for anonymous conversations, similar to Omegle but within Telegram.

## Features ✨

- **Anonymous Matching**: Connect random users for private conversations
- **Pseudonym System**: Each user gets a unique pseudonym for anonymity
- **Media Support**: Share photos, videos, audio, documents, and stickers
- **Skip Feature**: Find new partners with `/next` command
- **Thread-Safe**: Handles multiple users simultaneously
- **Error Handling**: Robust error handling and logging

## Prerequisites 📋

- Python 3.7 or higher
- A Telegram account
- Basic knowledge of Python (for customization)

## Setup Instructions 🚀

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Save the bot token (you'll need it later)

### 2. Install Dependencies

```bash
# Clone or download the project files
# Navigate to the project directory

# Install required packages
pip install -r requirements.txt

# Or install individually
pip install pyTelegramBotAPI python-dotenv
```

### 3. Configure the Bot

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and add your bot token:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   ADMIN_ID=your_telegram_user_id (optional)
   ```

### 4. Run the Bot

```bash
python anonymous_chat_bot.py
```

## Bot Commands 🤖

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | Show help information |
| `/find` | Find a random chat partner |
| `/next` | Skip current partner and find new one |
| `/stop` | End current chat or stop searching |

## How It Works 🔄

1. **User Registration**: Users start with `/start` command
2. **Partner Matching**: Users use `/find` to join the waiting queue
3. **Anonymous Chat**: Once matched, users can chat with pseudonyms
4. **Partner Switching**: Users can skip partners with `/next`
5. **Chat Ending**: Users can end chats with `/stop`

## Architecture 🏗️

### Core Components

- **AnonymousChatBot Class**: Main bot logic and handlers
- **User Management**: Waiting queue and active chat tracking
- **Pseudonym System**: Anonymous identity generation
- **Message Forwarding**: Secure message routing between partners

### Data Structures

```python
waiting_users: Set[int]           # Users waiting for partners
active_chats: Dict[int, int]      # user_id -> partner_id mapping
user_pseudonyms: Dict[int, str]   # user_id -> pseudonym mapping
```

### Thread Safety

The bot uses threading locks to ensure thread-safe operations when multiple users interact simultaneously.

## Customization Options 🎨

### Adding Profanity Filter

```python
FORBIDDEN_WORDS = ['word1', 'word2', 'word3']

def contains_forbidden_words(text):
    return any(word.lower() in text.lower() for word in FORBIDDEN_WORDS)
```

### Gender-Based Matching

```python
user_genders: Dict[int, str] = {}  # Track user genders

# Add gender selection in start command
# Modify matching logic to pair opposite genders
```

### Message Rate Limiting

```python
from time import time

user_last_message: Dict[int, float] = {}
RATE_LIMIT = 1  # seconds between messages

def is_rate_limited(user_id):
    now = time()
    if user_id in user_last_message:
        if now - user_last_message[user_id] < RATE_LIMIT:
            return True
    user_last_message[user_id] = now
    return False
```

## Deployment Options 🌐

### Local Development
```bash
python anonymous_chat_bot.py
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "anonymous_chat_bot.py"]
```

Build and run:
```bash
docker build -t anonymous-chat-bot .
docker run -d --env-file .env anonymous-chat-bot
```

### Cloud Deployment

Popular options:
- **Heroku**: Easy deployment with git integration
- **PythonAnywhere**: Simple Python hosting
- **DigitalOcean**: VPS with full control
- **AWS/GCP**: Scalable cloud solutions

## Security Considerations 🔒

1. **Token Security**: Never commit bot tokens to version control
2. **User Privacy**: No personal information is stored
3. **Message Logging**: Consider legal requirements for message storage
4. **Rate Limiting**: Implement to prevent spam
5. **Content Filtering**: Add profanity/inappropriate content filters

## Troubleshooting 🔧

### Common Issues

**Bot doesn't respond:**
- Check if bot token is correct
- Ensure bot is started (`/start` sent to bot)
- Check internet connection and firewall settings

**Users can't connect:**
- Verify bot is running and polling
- Check console for error messages
- Ensure threading locks aren't causing deadlocks

**Memory issues:**
- Implement periodic cleanup of old user data
- Add limits on maximum concurrent users
- Monitor memory usage in production

### Debug Mode

Add logging configuration:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is open source. You're free to use, modify, and distribute it.

## Disclaimer ⚠️

This bot is for educational purposes. Ensure compliance with:
- Telegram's Terms of Service
- Local privacy laws
- Content moderation requirements
- Data protection regulations

## Support 💬

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue on the repository
4. Contact the developer

---

**Happy Anonymous Chatting!** 🎉
