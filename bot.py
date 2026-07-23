import logging
import os
import tempfile
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Lazy agent initialization - NOT at module level to avoid crashing on Vercel import
_agent = None

def get_agent():
    """Lazily initializes the TaskAssistantAgent on first use."""
    global _agent
    if _agent is None:
        from agent import TaskAssistantAgent
        _agent = TaskAssistantAgent()
    return _agent

# Custom Reply Keyboard Buttons
KEYBOARD_TODAY = "📅 Bugungi rejalarni ko'rish"
KEYBOARD_ADD = "➕ Yangi vazifa qo'shish"
KEYBOARD_HELP = "❓ Yordam"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(KEYBOARD_TODAY), KeyboardButton(KEYBOARD_ADD)],
        [KeyboardButton(KEYBOARD_HELP)],
    ],
    resize_keyboard=True
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user_name = update.effective_user.first_name if update.effective_user else "Foydalanuvchi"
    
    welcome_text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        "Men sizning shaxsiy <b>AI Vazifalar Yordamchingizman</b>. 🤖📅\n"
        "Google Kalendaringiz bilan integratsiya qilinganman va vaqtingizni unumli rejalashtirishga yordam beraman.\n\n"
        "💡 <b>Men nimalar qila olaman?</b>\n"
        "• <b>Matn yuborishingiz mumkin:</b> <i>'Ertaga soat 15:00 da loyiha bo'yicha uchrashuv belgilagin'</i>\n"
        "• <b>Ovozli xabar yuborishingiz mumkin:</b> Shunchaki nima rejalashtirayotganingizni gapirib bering!\n"
        "• <b>Rejalarni ko'rish:</b> <i>'Bugungi va ertangi rejam qanday?'</i>\n\n"
        "Boshlash uchun quyidagi tugmalardan birini bosing yoki menga yozing/ovozli xabar yuboring!"
    )
    
    await update.message.reply_text(
        text=welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_KEYBOARD
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    help_text = (
        "❓ <b>Yordam va Qo'llanma</b>\n\n"
        "Siz menga har qanday ko'rinishda vazifalaringizni va rejalaringizni aytishingiz mumkin:\n\n"
        "📌 <b>Misollar:</b>\n"
        "1. <i>'Bugun soat 19:00 da sport zaliga borishim kerak'</i>\n"
        "2. <i>'Kelasi dushanba soat 10:00 da taqdimot tayyorlash vazifasini qo'sh'</i>\n"
        "3. <i>'Indinga soat 14:30 dagi uchrashuvni bekor qil'</i>\n"
        "4. <i>'Shu haftadagi barcha rejalarimni ko'rsat'</i>\n\n"
        "🎙 <b>Ovozli xabarlar:</b> Ovozli tugmani bosib, nima rejangiz borligini shunchaki gapirib yuboring — men uni o'zim kalendarga qo'shaman!"
    )
    
    await update.message.reply_text(
        text=help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_KEYBOARD
    )

async def send_safe_message(update: Update, text: str) -> None:
    """Sends a message, falling back to plain text if Markdown parsing fails."""
    try:
        await update.message.reply_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=MAIN_KEYBOARD
        )
    except Exception:
        await update.message.reply_text(
            text=text,
            reply_markup=MAIN_KEYBOARD
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages from the user."""
    user_text = update.message.text.strip()
    
    # Handle reply keyboard actions
    if user_text == KEYBOARD_TODAY:
        user_text = "Bugungi barcha rejam va tadbirlarimni ko'rsat."
    elif user_text == KEYBOARD_ADD:
        await update.message.reply_text(
            "Yangi vazifangizni matn yoki ovozli xabar ko'rinishida yuboring.\n"
            "<i>Masalan: 'Ertaga soat 16:00 da stomatologga borish'</i>",
            parse_mode=ParseMode.HTML
        )
        return
    elif user_text == KEYBOARD_HELP:
        await help_command(update, context)
        return

    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # Process with Gemini Agent
    try:
        agent = get_agent()
        response_text = agent.process_message(user_text)
        await send_safe_message(update, response_text)
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text(
            text=f"❌ Xatolik yuz berdi: {str(e)}",
            reply_markup=MAIN_KEYBOARD
        )

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming voice notes by downloading audio and passing it to Gemini."""
    voice = update.message.voice
    if not voice:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text("🎙 Ovozli xabar eshitilmoqda va tahlil qilinmoqda...")

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"voice_{voice.file_unique_id}.ogg")

    try:
        telegram_file = await context.bot.get_file(voice.file_id)
        await telegram_file.download_to_drive(file_path)

        agent = get_agent()
        response_text = agent.process_voice(file_path)

        await status_msg.delete()
        await send_safe_message(update, response_text)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await status_msg.edit_text(f"❌ Ovozli xabarni ishlashda xatolik yuz berdi: {str(e)}")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


def main():
    """Main entrypoint to start the Telegram bot in polling mode (local development)."""
    config.validate_config()

    print("🚀 Telegram AI Task Assistant Bot ishga tushmoqda...")

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
