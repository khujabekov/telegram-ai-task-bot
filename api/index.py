import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from bot import start_command, help_command, handle_text_message, handle_voice_message

# Build application once
telegram_app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
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
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html_response = (
            "<h2>🤖 Telegram AI Task Assistant Bot Vercel'da muvaffaqiyatli ishlayapti!</h2>"
            "<p>Webhook joylashtirilgan. Bot Telegram'dan kelgan so'rovlarni qabul qilmoqda.</p>"
        )
        self.wfile.write(html_response.encode("utf-8"))
