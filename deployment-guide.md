# Telegram Anonymous Chat Bot Deployment Guide

## Environment Setup

Create a `.env` file in your project root:

```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321
ENCRYPTION_KEY=your_base64_encoded_fernet_key
PORT=8443
WEBHOOK_URL=https://your-render-app.onrender.com
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run locally:
```bash
python telegram-anonymous-bot.py
```

## Render Deployment

### 1. Create Render Web Service

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure build and start commands:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app --host 0.0.0.0 --port $PORT
```

### 2. Environment Variables

Set these in Render dashboard:

- `BOT_TOKEN`: Your bot token from BotFather
- `ADMIN_IDS`: Comma-separated admin user IDs
- `ENCRYPTION_KEY`: Generated Fernet key for message encryption
- `PORT`: 8443 (Render will override this)

### 3. Generate Encryption Key

Run this Python code to generate a secure key:

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

Copy the output to your `ENCRYPTION_KEY` environment variable.

### 4. Set Webhook

After deployment, set your webhook URL:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RENDER_URL>"
```

Replace:
- `<YOUR_BOT_TOKEN>` with your actual bot token
- `<YOUR_RENDER_URL>` with your Render app URL

## GitHub Repository Structure

```
telegram-anonymous-bot/
├── telegram-anonymous-bot.py
├── requirements.txt
├── main.py (for webhook deployment)
├── .env (local only - not committed)
├── .gitignore
└── README.md
```

## Webhook Version (main.py)

For Render deployment with webhooks:

```python
from flask import Flask, request, jsonify
import asyncio
import threading
from telegram import Update
from telegram.ext import Application
import json
import os

# Import your bot class
from telegram_anonymous_bot import AnonymousChatBot, Config

app = Flask(__name__)

# Initialize bot
bot_instance = AnonymousChatBot()
application = Application.builder().token(Config.BOT_TOKEN).build()

# Add all handlers here (same as in main bot file)
# ... handler setup ...

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.create_task(application.process_update(update))
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8443))
    app.run(host='0.0.0.0', port=port)
```

## Features Implemented

### Privacy & Security
- ✅ Anonymous user IDs (USER1234 format)
- ✅ End-to-end message encryption
- ✅ No personal data storage
- ✅ Session timeouts
- ✅ Message expiry (24 hours)

### Anti-Spam & Moderation
- ✅ Rate limiting (10 messages/minute)
- ✅ Profanity filtering
- ✅ User reporting system
- ✅ Warning system (3 strikes)
- ✅ Temporary/permanent bans

### Admin Controls
- ✅ `/ban <user_id>` - Ban users
- ✅ `/unban <user_id>` - Unban users
- ✅ `/status` - Bot statistics
- ✅ Admin activity logging

### User Commands
- ✅ `/start` - Register and get anonymous ID
- ✅ `/find` - Find random chat partner
- ✅ `/stop` - End current conversation
- ✅ `/report` - Report inappropriate users
- ✅ `/help` - Show help information

### Technical Features
- ✅ SQLite logging database
- ✅ Queue-based user matching
- ✅ Session management
- ✅ Background cleanup tasks
- ✅ Error handling & logging

## Testing Your Bot

1. Message @BotFather to create your bot
2. Get the bot token
3. Set up environment variables
4. Deploy to Render
5. Set webhook URL
6. Test commands:
   - `/start` to register
   - `/find` to start matching
   - Send messages in chat
   - `/report` to test reporting
   - `/stop` to end chat

## Security Considerations

1. **Environment Variables**: Never commit tokens or keys to Git
2. **HTTPS Only**: Render provides HTTPS by default
3. **Rate Limiting**: Prevents spam and abuse
4. **Input Validation**: All user inputs are validated
5. **Error Handling**: Graceful error handling prevents crashes
6. **Logging**: Audit trail for admin actions

## Monitoring & Maintenance

- Check Render logs for errors
- Monitor database size (SQLite)
- Regular security updates
- User feedback and improvements

## Troubleshooting

**Bot not responding:**
- Check webhook URL is correct
- Verify environment variables
- Check Render logs

**Database errors:**
- Ensure SQLite is properly initialized
- Check file permissions

**Rate limiting issues:**
- Adjust `MAX_MESSAGES_PER_MINUTE` in config
- Clear rate limiter cache if needed

**Memory issues:**
- Implement periodic cleanup
- Use Redis for production scaling