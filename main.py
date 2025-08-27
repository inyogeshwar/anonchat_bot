#!/usr/bin/env python3
"""
Simple Telegram Bot with Flask Webhook
Author: Your Name
Description: A minimal Telegram bot that responds to /start and echoes messages.
"""

import os
import json
import logging
import threading
import asyncio

from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-bot-token-here")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Initialize Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# /start command handler
async def start_command(update: Update, context):
    await update.message.reply_text(
        "👋 Hello! I’m a simple bot. Send me any message and I’ll echo it back."
    )

# Echo message handler
async def echo_message(update: Update, context):
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")

# Register handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

@app.route("/", methods=["GET"])
def index():
    return "<h1>Simple Telegram Bot is running!</h1>"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_data(as_text=True)
        update = Update.de_json(json.loads(data), application.bot)
        # Schedule handling asynchronously
        asyncio.get_event_loop().create_task(application.process_update(update))
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/set-webhook", methods=["POST"])
def set_webhook():
    try:
        url = f"{WEBHOOK_URL}/webhook"
        result = application.bot.set_webhook(url=url)
        return jsonify({"status": "webhook_set", "url": url, "result": result})
    except Exception as e:
        logger.error("Set webhook error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

def run_background_tasks():
    # Placeholder for any background tasks if needed
    pass

if __name__ == "__main__":
    # Start background thread for tasks
    threading.Thread(target=run_background_tasks, daemon=True).start()

    # Determine port for Flask
    port = int(os.environ.get("PORT", 8443))
    logger.info("Starting Flask server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
