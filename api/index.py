import json
import asyncio
import os
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config

_telegram_app = None

def get_telegram_app():
    global _telegram_app
    if _telegram_app is None:
        if not config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing! Please set it in Vercel Environment Variables.")
        
        # Import handlers lazily
        from bot import start_command, help_command, handle_text_message, handle_voice_message

        app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
        _telegram_app = app
    return _telegram_app

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            telegram_app = get_telegram_app()

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            update = Update.de_json(data, telegram_app.bot)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(telegram_app.initialize())
                loop.run_until_complete(telegram_app.process_update(update))
            finally:
                loop.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        bot_token_status = "✅ O'rnatilgan" if config.TELEGRAM_BOT_TOKEN else "❌ Kiritilmagan"
        gemini_status = "✅ O'rnatilgan" if config.GEMINI_API_KEY else "❌ Kiritilmagan"
        token_json_status = "✅ O'rnatilgan" if os.getenv("GOOGLE_TOKEN_JSON") else "⚠️ Kiritilmagan (Vercel Environment Variables'ga GOOGLE_TOKEN_JSON kiriting)"

        html_response = f"""
        <html>
        <head><title>Telegram Bot Vercel Status</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2>🤖 Telegram AI Task Assistant Bot (Vercel Webhook)</h2>
            <p><strong>Holat:</strong> ✅ Serverless funksiya ishlayapti</p>
            <hr>
            <h3>Environment Variables holati:</h3>
            <ul>
                <li><strong>TELEGRAM_BOT_TOKEN:</strong> {bot_token_status}</li>
                <li><strong>GEMINI_API_KEY:</strong> {gemini_status}</li>
                <li><strong>GOOGLE_TOKEN_JSON:</strong> {token_json_status}</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html_response.encode("utf-8"))
