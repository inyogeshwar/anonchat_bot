#!/bin/bash

# Deployment script for Anonymous Chat Bot

echo "🚀 Starting Anonymous Chat Bot Deployment"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env file and add your bot token before running the bot."
    echo "📝 You can edit it with: nano .env"
    exit 1
fi

# Check if bot token is configured
if grep -q "your_bot_token_from_botfather" .env; then
    echo "❌ Bot token not configured in .env file"
    echo "📝 Please edit .env file and replace 'your_bot_token_from_botfather' with your actual bot token"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo "🤖 Starting the bot..."
echo "📋 Use Ctrl+C to stop the bot"

# Run the bot
python3 anonymous_chat_bot.py
