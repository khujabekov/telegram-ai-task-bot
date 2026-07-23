# 🤖 Telegram AI Task Assistant Bot (Google Calendar + Gemini)

Ushbu loyiha — O'zbek tilida tabiiy matn va ovozli xabarlarni tushunadigan, Sun'iy Intellekt (Google Gemini 1.5) va Google Kalendar integratsiyasiga ega mukammal Telegram Bot.

---

## 🌟 Imkoniyatlar
-  Uzbek tilidagi **matnli** va **ovozli xabarlarni (Voice Notes)** tushunish.
- **Nisbiy vaqtlarni aniq hisoblash**: "bugun", "ertaga", "indinga", "kelasi dushanba", "kechqurun soat 8 da" va h.k.
- **Google Calendar CRUD**:
  - ➕ Yangi vazifa/tadbirlar qo'shish (`add_event`).
  - 📅 Bo'lajak rejalarni ko'rish va ro'yxat shaklida chiqarish (`get_upcoming_events`).
  - 🗑 Rejalarni o'chirish (`delete_event`).
- **Multimodal AI**: Telegram ovozli xabarlarini to'g'ridan-to me Gemini o'qib beradi va kalendar amallarini bajaradi.
- **Vaqt mintaqasi**: `Asia/Tashkent` (sozlanishi mumkin).

---

## 📁 Loyiha Tuzilishi

```
Telegram AI Task Assistant Bot/
├── config.py              # Atrof-muhit o'zgaruvchilari va sozlamalar
├── bot.py                 # Telegram Bot voqea ishlovchilari (handlers)
├── agent.py               # Gemini AI Agenti (Uzbek prompt + Tool Calling + Voice)
├── calendar_service.py    # Google Calendar API wrapper (OAuth2 authentication)
├── requirements.txt       # Python kutubxonalar ro'yxati
├── .env.example           # API kalitlar uchun andoza
└── README.md              # Qo'llanma
```

---

## 🛠 O'rnatish va Sozlash Yo'riqnomasi

### 1. Rejimlarni yuklab olish va Virtual Muhit (venv) yaratish

Terminal yoki komandalar satrida quyidagi buyruqlarni bajaring:

```bash
# Python virtual muhitini yaratish
python -m venv venv

# Virtual muhitni faollashtirish (Windows):
venv\Scripts\activate

# Virtual muhitni faollashtirish (Linux/macOS):
source venv/bin/activate
```

### 2. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

---

### 3. API Kalitlarni Olish

#### A. Telegram Bot Token olish:
1. Telegram'da [@BotFather](https://t.me/BotFather) botiga o'ting.
2. `/newbot` buyrug'ini yuboring va botingizga nom hamda username bering.
3. BotFather bergan **HTTP API Token** kodi nusxasini oling.

#### B. Google Gemini API Key olish:
1. [Google AI Studio](https://aistudio.google.com/) platformasiga kiring.
2. **Create API key** tugmasini bosing va API kalit yaratib, nusxasini oling.

#### C. Google Calendar OAuth Credentials (`credentials.json`) olish:
1. [Google Cloud Console](https://console.cloud.google.com/) platformasiga kiring.
2. Yangi loyiha yarating (masalan: `Telegram-Task-Bot`).
3. Chap menyudan **APIs & Services** > **Library** bo'limiga o'ting va **Google Calendar API** ni qidirib, **Enable** qiling.
4. **OAuth consent screen** bo'limiga o'tib, **External** turini tanlang va asosiy ma'lumotlarni to'ldiring (Test users qismiga o'z bosingizdagi Gmail manzilingizni qo me'shing).
5. **Credentials** bo'limiga o'ting -> **Create Credentials** -> **OAuth client ID** tanlang.
6. Application type: **Desktop app** deb belgilang va nom bering.
7. Yaratilgan OAuth Client'ni **JSON farmatida yuklab oling** va nomini `credentials.json` qilib o me'zgartirib, loyiha papkasiga joylashtiring.

---

### 4. `.env` Faylini Sozlash

Loyiha ildiz papkasida `.env` faylini yarating (`.env.example` dan nusxalab) va o'z kalitlaringizni kiriting:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
TIMEZONE=Asia/Tashkent
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
```

---

## 🚀 Botni Ishga Tushirish

Botni ishga tushirish uchun quyidagi buyruqni bajaring:

```bash
python bot.py
```

> ⚠️ **Birinchi marta ishga tushirilganda**:
> Google Calendar API avtorizatsiyadan o'tish uchun brauzeringizda oyna ochiladi (yoki havola ko'rsatiladi). Google hisobingizga kirib, ruxsat bering. Ruxsat berilgach, avtomatik tarzda loyiha papkasida `token.json` fayli yaratiladi va keyingi safar qayta avtorizatsiya so'ralmaydi.

---

## 💬 Ishlatish Misollari

### Matnli xabarlar:
- `Ertaga soat 15:00 da loyiha muhokamasi bo'yicha uchrashuv belgilagin`
- `Bugungi rejam qanday?`
- `Kelasi dushanba ertalab 09:00 da taqdimot tayyorlash vazifasini qo'sh`
- `Id: abc123xyz bo'lgan tadbirni o'chir`

### Ovozli xabarlar (Voice Notes):
- Telegram'da ovozli xabar tugmasini bosing va uzbek tilida gapiring:
  *(Masalan: "Ertaga soat ikki yarimda do'stlarim bilan kofe ichgani boraman, shuni kalendarga eslatma qilib qo'sh")*
- Bot ovozni avtomatik tahlil qiladi va Google Kalendaringizga kiritib, tasdiqlovchi javob beradi.

---

## 🛡 Xatoliklar va Troubleshooting

- `Missing required environment variables`: `.env` faylida kalitlar to'liq kiritilganini tekshiring.
- `Google credentials file not found`: `credentials.json` fayli loyiha ildizida joylashganiga ishonch hosil qiling.
- `Token Expired`: `token.json` faylini o'chirib, `python bot.py` ni qayta run qiling va avtorizatsiyadan yangitdan o'ting.

---

## 📜 Litsenziya
MIT License. Erkin foydalanishingiz mumkin!
