import datetime
import re
import pytz
from typing import Optional
import google.generativeai as genai

import config
from calendar_service import get_calendar_service

# --- Tool functions for Gemini Function Calling ---

def add_calendar_event(title: str, start_time: str, end_time: str = None, details: str = None) -> str:
    """
    Google Kalendarga yangi tadbir yoki vazifa qo'shadi.
    
    Args:
        title: Tadbir sarlavhasi yoki nomi (masalan: 'Loyiha uchrashuvi').
        start_time: Boshlanish vaqti ISO formatida (masalan: '2026-07-24T14:00:00').
        end_time: Qoshimcha tugash vaqti ISO formatida. Agar berilmasa, boshlanishidan 1 soat keyin bo'ladi.
        details: Qoshimcha ma'lumotlar yoki izohlar.
    """
    try:
        service = get_calendar_service()
        result = service.add_event(title, start_time, end_time, details)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"

def get_calendar_events(limit: int = 5, start_date: str = None) -> str:
    """
    Google Kalendardagi bo'lajak tadbir va rejalarni oladi.
    
    Args:
        limit: Qaytariladigan tadbirlar soni (standart 5).
        start_date: Qaysi sanadan boshlab qidirish kerakligi ISO formatida (masalan: '2026-07-24T00:00:00').
    """
    try:
        service = get_calendar_service()
        result = service.get_upcoming_events(limit=limit, start_date=start_date)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"

def delete_calendar_event(event_id: str) -> str:
    """
    Google Kalendardagi tadbirni ID raqami bo'yicha o'chiradi.
    
    Args:
        event_id: O'chirilishi kerak bo'lgan tadbirning bitta-bittalik ID kodi.
    """
    try:
        service = get_calendar_service()
        result = service.delete_event(event_id)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"

def add_task(title: str, due_date: str = None, notes: str = None) -> str:
    """
    Google Tasks-ga (vazifalar ro'yxatiga) yangi oddiy vazifa (to-do) qo'shadi.
    
    Args:
        title: Vazifa nomi yoki tavsifi (masalan: 'Kitob o'qish' yoki 'Sut sotib olish').
        due_date: Qoshimcha bajarilish sanasi ISO formatida (masalan: '2026-07-26T18:00:00').
        notes: Vazifa bo'yicha qoshimcha izoh.
    """
    try:
        service = get_calendar_service()
        result = service.add_task(title, due_date, notes)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"

def get_tasks(limit: int = 5, show_completed: bool = False) -> str:
    """
    Google Tasks-dagi bajarilishi kerak bo'lgan vazifalar ro'yxatini oladi.
    
    Args:
        limit: Qaytariladigan vazifalar soni (standart 5).
        show_completed: Bajarilgan vazifalarni ham ko'rsatish (standart False).
    """
    try:
        service = get_calendar_service()
        result = service.get_tasks(limit=limit, show_completed=show_completed)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"

def complete_task(task_id: str) -> str:
    """
    Google Tasks-dagi vazifani bajarildi (Done) deb belgilaydi.
    
    Args:
        task_id: Bajarilgan deb belgilanishi kerak bo'lgan vazifaning ID kodi.
    """
    try:
        service = get_calendar_service()
        result = service.complete_task(task_id)
        return str(result)
    except Exception as e:
        return f"Xatolik: {e}"


class TaskAssistantAgent:
    """Gemini AI agent that processes text and voice messages with calendar & tasks tool calling."""

    def __init__(self):
        self.tz = pytz.timezone(config.TIMEZONE)
        self.tools = [
            add_calendar_event, get_calendar_events, delete_calendar_event,
            add_task, get_tasks, complete_task
        ]
        self.model_name = config.GEMINI_MODEL_NAME  # Use configured model directly
        
        # Configure Gemini
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)

    def _format_error(self, e: Exception) -> str:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return (
                "⚠️ Gemini API Kalitida Xatolik!\n\n"
                ".env faylidagi GEMINI_API_KEY xato yoki yaroqsiz kiritilgan.\n\n"
                "Yechim:\n"
                "1. https://aistudio.google.com/app/apikey saytiga kiring.\n"
                "2. Yangi API Key oling.\n"
                "3. .env fayliga qo'ying va botni qayta ishga tushiring."
            )
        if "429" in error_msg or "quota" in error_msg.lower():
            retry_match = re.search(r"retry in ([\d.]+)s", error_msg, re.IGNORECASE)
            wait_hint = str(int(float(retry_match.group(1)))) if retry_match else "30"
            return (
                f"⏳ Gemini API kvotasi vaqtincha to'ldi. Taxminan {wait_hint} soniyadan keyin qayta urinib ko'ring.\n\n"
                "💡 Bepul tarifda 1 daqiqada maksimal 15 marta so'rov yuborish mumkin."
            )
        if "404" in error_msg and "not found" in error_msg.lower():
            return (
                f"⚠️ Model topilmadi: {self.model_name}\n\n"
                "GEMINI_MODEL_NAME ni tekshiring (masalan: gemini-2.0-flash)."
            )
        return f"❌ Xatolik yuz berdi: {error_msg}"

    def _build_system_instruction(self) -> str:
        """Generates dynamic system instructions containing current local datetime."""
        now = datetime.datetime.now(self.tz)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S (%A)")
        
        return (
            f"Siz Google Kalendar va Google Tasks-ni boshqaruvchi Telegram AI yordamchisiz. Vaqt: {now_str}.\n"
            "Qoidalar:\n"
            "1. Doimo o'zbek tilida muloyim, ixcham va aniq javob bering.\n"
            "2. Mos tool'larni chaqiring:\n"
            "   - Aniq vaqtli tadbir/majlis: add_calendar_event, get_calendar_events, delete_calendar_event\n"
            "   - Oddiy vazifa/To-Do list: add_task(title, due_date, notes), get_tasks(limit, show_completed), complete_task(task_id)\n"
            "3. Telegram markdown belgilardan (*, _, `) foydalanmang."
        )

    def _create_model(self):
        """Creates a Gemini GenerativeModel instance."""
        genai.configure(api_key=config.GEMINI_API_KEY)
        generation_config = {
            "temperature": 0.2,
            "max_output_tokens": 1000
        }
        return genai.GenerativeModel(
            model_name=self.model_name,
            tools=self.tools,
            system_instruction=self._build_system_instruction(),
            generation_config=generation_config
        )

    def process_message(self, user_text: str) -> str:
        """Processes text messages from the user using Gemini with Tool Calling."""
        try:
            model = self._create_model()
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(user_text)
            return response.text
        except Exception as e:
            return self._format_error(e)

    def process_voice(self, audio_file_path: str) -> str:
        """Processes voice messages by sending inline audio bytes directly to Gemini."""
        try:
            with open(audio_file_path, "rb") as f:
                audio_bytes = f.read()

            audio_part = {"mime_type": "audio/ogg", "data": audio_bytes}
            prompt = "Ovozli xabarni tushunib, kerakli kalendar tool'ini chaqiring va o'zbekcha javob bering."

            model = self._create_model()
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message([audio_part, prompt])
            return response.text
        except Exception as e:
            return self._format_error(e)
