import os
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, filters

# Load environment variables from .env file
load_dotenv()

# Retrieve values from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS").split(",")  # Assuming a comma-separated list of admin IDs
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT"))

user_pairs = {}

def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message and instructions when a user starts the bot."""
    update.message.reply_text("Welcome to the Anonymous Chat Bot!\nType any message to find an anonymous chat partner.")

def anonymous_chat(update: Update, context: CallbackContext) -> None:
    """Handles the anonymous chat between users."""
    user_id = update.message.from_user.id
    text = update.message.text

    # If the user is already in a conversation, send the message to the partner
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        context.bot.send_message(partner_id, text)
        update.message.reply_text("Message sent to your anonymous partner!")
    else:
        # Find a new partner for the user
        available_users = [user for user in user_pairs.values() if user != user_id]
        if not available_users:
            user_pairs[user_id] = None  # Mark user as available for pairing
            update.message.reply_text("Waiting for another user to pair with you...")
            return
        
        partner_id = random.choice(available_users)
        user_pairs[user_id] = partner_id
        user_pairs[partner_id] = user_id
        context.bot.send_message(partner_id, "You have a new anonymous partner! Start chatting.")
        update.message.reply_text("You are now paired with an anonymous partner. Start chatting!")

def stop(update: Update, context: CallbackContext) -> None:
    """Stop the anonymous chat and unpair users."""
    user_id = update.message.from_user.id
    if user_id in user_pairs:
        partner_id = user_pairs.pop(user_id, None)
        if partner_id:
            user_pairs.pop(partner_id, None)
            context.bot.send_message(partner_id, "Your anonymous partner has left the conversation.")
        update.message.reply_text("You have left the chat.")
    else:
        update.message.reply_text("You are not currently in a chat.")

def main() -> None:
    """Start the bot and set up the command handlers."""
    updater = Updater(BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anonymous_chat))

    # Webhook setup (if you're using a server with a webhook)
    if WEBHOOK_URL:
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN)
        updater.bot.set_webhook(WEBHOOK_URL)
    else:
        # Default polling method if webhook is not set
        updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
