#!/usr/bin/env python3
from flask import Flask, request, jsonify
import asyncio
import threading
import os
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram_anonymous_bot import AnonymousChatBot, Config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize bot instance and application
bot_instance = AnonymousChatBot()
application = Application.builder().token(Config.BOT_TOKEN).build()

# Register user commands
application.add_handler(CommandHandler("start", bot_instance.start_command))
application.add_handler(CommandHandler("find", bot_instance.find_partner_command))
application.add_handler(CommandHandler("stop", bot_instance.stop_chat_command))
application.add_handler(CommandHandler("report", bot_instance.report_command))
application.add_handler(CommandHandler("help", bot_instance.help_command))

# Register admin commands
application.add_handler(CommandHandler("ban", bot_instance.ban_command))
application.add_handler(CommandHandler("unban", bot_instance.unban_command))
application.add_handler(CommandHandler("status", bot_instance.status_command))

# Register message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.handle_message))

@app.route("/", methods=["GET"])
def index():
    return (
        "<h1>Anonymous Telegram Chat Bot</h1>"
        "<p>Bot is running and ready to receive webhooks.</p>"
        '<ul>'
        '<li><a href="/health">Health Check</a></li>'
        "<li>Webhook endpoint: /webhook</li>"
        "</ul>"
    )

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "bot_username": application.bot.username or "unknown"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_data(as_text=True)
        update = Update.de_json(json.loads(data), application.bot)
        asyncio.get_event_loop().create_task(application.process_update(update))
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/set-webhook", methods=["POST"])
def set_webhook():
    try:
        url = f"{Config.WEBHOOK_URL}/webhook"
        result = application.bot.set_webhook(url=url)
        return jsonify({"status": "webhook_set", "url": url, "result": result})
    except Exception as e:
        logger.error("Set webhook error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

def start_cleanup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_instance.cleanup_expired_messages())

if __name__ == "__main__":
    # Launch cleanup task
    threading.Thread(target=start_cleanup, daemon=True).start()

    port = int(os.environ.get("PORT", 8443))
    logger.info("Starting Flask server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
