from flask import Flask, request, jsonify
import asyncio
import threading
from telegram import Update
from telegram.ext import Application
import json
import os
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'your-bot-token-here')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

# Import bot components
from telegram_anonymous_bot import AnonymousChatBot

# Initialize bot
bot_instance = AnonymousChatBot()
application = Application.builder().token(Config.BOT_TOKEN).build()

# Add handlers
from telegram.ext import CommandHandler, MessageHandler, filters

application.add_handler(CommandHandler("start", bot_instance.start_command))
application.add_handler(CommandHandler("find", bot_instance.find_partner_command))
application.add_handler(CommandHandler("stop", bot_instance.stop_chat_command))
application.add_handler(CommandHandler("report", bot_instance.report_command))
application.add_handler(CommandHandler("help", bot_instance.help_command))

# Admin handlers
application.add_handler(CommandHandler("ban", bot_instance.ban_command))
application.add_handler(CommandHandler("unban", bot_instance.unban_command))
application.add_handler(CommandHandler("status", bot_instance.status_command))

# Message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.handle_message))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates"""
    try:
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json.loads(json_string), application.bot)
        
        # Process the update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bot_username': application.bot.username if application.bot else 'unknown'
    })

@app.route('/setwwebhook', methods=['POST'])
def set_webhook():
    """Endpoint to set webhook (for convenience)"""
    try:
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        response = application.bot.set_webhook(url=webhook_url)
        return jsonify({'status': 'webhook_set', 'url': webhook_url, 'response': response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Basic index page"""
    return """
    <h1>Anonymous Telegram Chat Bot</h1>
    <p>Bot is running and ready to receive webhooks.</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li>Webhook endpoint: /webhook</li>
    </ul>
    """

def start_cleanup_task():
    """Start the cleanup background task"""
    def run_cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_instance.cleanup_expired_messages())
    
    cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    # Start background cleanup task
    start_cleanup_task()
    
    # Get port from environment
    port = int(os.environ.get('PORT', 8443))
    
    logger.info(f"Starting webhook server on port {port}")
    logger.info(f"Webhook URL: {Config.WEBHOOK_URL}/webhook")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)