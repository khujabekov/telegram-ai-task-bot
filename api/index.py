import json
import asyncio
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

# Add project root to Python path so imports work from api/ subdirectory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config

_telegram_app = None
_init_error = None

def get_telegram_app():
    """Lazily builds the Telegram Application with all handlers."""
    global _telegram_app, _init_error
    
    if _init_error:
        raise _init_error
    
    if _telegram_app is not None:
        return _telegram_app

    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
        )
        from bot import start_command, help_command, handle_text_message, handle_voice_message

        if not config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing!")

        app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
        _telegram_app = app
        return app
        
    except Exception as e:
        _init_error = e
        raise


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handles incoming Telegram webhook POST requests."""
        try:
            from telegram import Update
            
            telegram_app = get_telegram_app()

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            update = Update.de_json(data, telegram_app.bot)

            # Run async handlers in a fresh event loop
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
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
            
            # Always return 200 to Telegram to prevent retry storms
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": error_msg}).encode("utf-8"))

    def do_GET(self):
        """Health check and diagnostic page."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        bot_ok = "✅" if config.TELEGRAM_BOT_TOKEN else "❌"
        gemini_ok = "✅" if config.GEMINI_API_KEY else "❌"
        token_ok = "✅" if os.getenv("GOOGLE_TOKEN_JSON") else "❌"

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Bot Status</title>
<style>body{{font-family:system-ui;max-width:500px;margin:40px auto;padding:20px}}
li{{margin:8px 0}}h2{{color:#333}}</style></head>
<body>
<h2>🤖 Telegram AI Task Assistant Bot</h2>
<p><b>Holat:</b> ✅ Serverless funksiya ishlayapti</p>
<p><b>Model:</b> {config.GEMINI_MODEL_NAME}</p>
<hr>
<h3>Environment Variables:</h3>
<ul>
<li><b>TELEGRAM_BOT_TOKEN:</b> {bot_ok}</li>
<li><b>GEMINI_API_KEY:</b> {gemini_ok}</li>
<li><b>GOOGLE_TOKEN_JSON:</b> {token_ok}</li>
</ul>
</body></html>"""
        self.wfile.write(html.encode("utf-8"))
