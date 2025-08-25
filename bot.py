# bot.py
import logging
import os
import json
from aiogram import Bot, Dispatcher, executor, types
from functools import wraps

# --- Импорты конфигурации и сервисов ---
from my_config import TELEGRAM_BOT_TOKEN
from user_config import AUTHORIZED_USERS, ADMIN_USERNAME
from services.gspread_service import add_note_to_sheet, get_service_account_email
from services.speech_to_text import speech_to_text
from services.trello_service import create_trello_card

# --- Настройка ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)
USER_SHEETS_FILE = 'user_sheets.json'

# --- Хранилище настроек пользователей ---
def load_user_sheets():
    """Загружает настройки пользователей из JSON-файла."""
    if not os.path.exists(USER_SHEETS_FILE):
        return {}
    with open(USER_SHEETS_FILE, 'r') as f:
        return json.load(f)

def save_user_sheets(data):
    """Сохраняет настройки пользователей в JSON-файл."""
    with open(USER_SHEETS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_sheets = load_user_sheets()

# --- Декоратор для проверки авторизации ---
def authorized_only(handler):
    """Декоратор, который пропускает к выполнению только авторизованных пользователей."""
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id not in AUTHORIZED_USERS:
            logging.warning(f"Неавторизованный доступ от пользователя {message.from_user.id} ({message.from_user.username}).")
            await message.reply(f"❌ **Доступ запрещен.**\n\nЭтот бот является приватным. Для получения доступа обратитесь к администратору: {ADMIN_USERNAME}")
            return
        return await handler(message, *args, **kwargs)
    return wrapper

# --- Команды бота ---
@dp.message_handler(commands=['start', 'help'])
@authorized_only
async def send_welcome(message: types.Message):
    """
    Обработчик команд /start и /help.
    Содержит подробную инструкцию по настройке.
    """
    user_id = str(message.from_user.id)
    sheet_url = user_sheets.get(user_id)
    
    service_email = get_service_account_email()
    if not service_email:
        await message.answer("Ошибка: не удается прочитать `credentials.json`. Обратитесь к администратору.")
        return

    instructions = (
        f"👋 **Привет! Это твой бот для заметок.**\n\n"
        f"Чтобы я мог сохранять твои мысли в Google Таблицу, нужно выполнить 3 простых шага:\n\n"
        f"**Шаг 1: Скопируй мой email** 📧\n"
        f"Мой уникальный адрес для доступа к Google-сервисам:\n"
        f"`{service_email}`\n\n"
        f"**Шаг 2: Создай и поделись Google Таблицей** 📝\n"
        f"   1. Перейди на [sheets.google.com](https://sheets.google.com/) и создай новую таблицу.\n"
        f"   2. Нажми синюю кнопку **'Настройки доступа'** (`Share`) в правом верхнем углу.\n"
        f"   3. Вставь мой email, который ты скопировал на Шаге 1.\n"
        f"   4. Выбери для меня роль **'Редактор'** (`Editor`) и нажми 'Отправить'.\n\n"
        f"**Шаг 3: Привяжи таблицу ко мне** 🔗\n"
        f"**Скопируй полную ссылку** из адресной строки браузера и отправь мне ее с командой:\n"
        f"`/set_sheet https://docs.google.com/spreadsheets/d/....`\n\n"
        f"После этого просто отправляй мне любой текст или голосовое сообщение, и я всё запишу!\n\n"
        f"---"
    )

    if sheet_url:
        instructions += f"\n✅ **Текущая таблица:** [Ссылка на таблицу]({sheet_url})"
    else:
        instructions += f"\n❌ **Статус:** Таблица еще не настроена."
        
    await message.answer(instructions, parse_mode='Markdown', disable_web_page_preview=True)


@dp.message_handler(commands=['set_sheet'])
@authorized_only
async def set_sheet(message: types.Message):
    """Устанавливает Google Таблицу для пользователя по ссылке."""
    user_id = str(message.from_user.id)
    sheet_url = message.get_args()
    if not sheet_url or not sheet_url.startswith('https://docs.google.com/spreadsheets/d/'):
        await message.reply("Пожалуйста, отправьте валидную ссылку на Google Таблицу после команды.\nПример: `/set_sheet https://...`")
        return
        
    user_sheets[user_id] = sheet_url
    save_user_sheets(user_sheets)
    logging.info(f"Пользователь {user_id} установил таблицу: '{sheet_url}'")
    await message.reply(f"✅ Отлично! Теперь все заметки будут сохраняться в эту таблицу.", parse_mode='Markdown')

@dp.message_handler(commands=['my_sheet'])
@authorized_only
async def my_sheet(message: types.Message):
    """Показывает текущую настроенную таблицу."""
    user_id = str(message.from_user.id)
    sheet_url = user_sheets.get(user_id)
    if sheet_url:
        await message.reply(f"Текущая таблица для записи: [Ссылка на таблицу]({sheet_url})", parse_mode='Markdown')
    else:
        await message.reply("Таблица еще не настроена. Используй команду `/set_sheet`.")

# --- Основная логика обработки ---
async def process_note(message: types.Message, text: str):
    """Общая логика для обработки и сохранения заметки."""
    user_id = str(message.from_user.id)
    sheet_url = user_sheets.get(user_id)
    
    if not sheet_url:
        await message.reply("⚠️ **Сначала нужно настроить таблицу!**\n\nИспользуй команду `/help`, чтобы увидеть инструкцию.")
        return
        
    # Шаг 1: Сохраняем в Google Sheets
    sheets_success = add_note_to_sheet(text, sheet_url)
    
    if sheets_success:
        # Шаг 2: Если в Sheets сохранилось, пробуем создать карточку в Trello
        trello_success = create_trello_card(text)
        
        if trello_success:
            await message.reply("✅ Записал в Google Sheets и создал карточку в Trello!")
        else:
            await message.reply("✅ Записал в Google Sheets.")
    else:
        await message.reply("❌ **Ошибка при записи в Google Sheets!**\n\nПроверь, что:\n1. Ссылка на таблицу верная.\n2. Ты дал права редактора моему сервисному email.")

# --- Обработчики сообщений ---
@dp.message_handler(content_types=types.ContentType.TEXT)
@authorized_only
async def handle_text(message: types.Message):
    """Ловит текстовые сообщения."""
    logging.info(f"Получен текст от {message.from_user.id}: '{message.text}'")
    await process_note(message, message.text)

@dp.message_handler(content_types=types.ContentType.VOICE)
@authorized_only
async def handle_voice(message: types.Message):
    """Ловит голосовые сообщения."""
    logging.info(f"Получено голосовое от {message.from_user.id}.")
    os.makedirs('temp', exist_ok=True)
    voice_file_path = os.path.join('temp', f"{message.voice.file_id}.ogg")
    
    try:
        await message.voice.download(destination_file=voice_file_path)
        logging.info(f"Голосовое сохранено: {voice_file_path}")
        await message.reply("⏳ Распознаю...")
        recognized_text = speech_to_text(voice_file_path)
        logging.info(f"Распознанный текст: '{recognized_text}'")

        # Проверяем, что текст не пустой
        if recognized_text and recognized_text.strip() and recognized_text != "Не удалось распознать речь.":
            await process_note(message, recognized_text)
        else:
            await message.reply("Не смог распознать речь в голосовом сообщении.")

    except Exception as e:
        logging.error(f"Ошибка обработки голосового: {e}")
        await message.reply("❌ Не удалось обработать голосовое сообщение.")
    finally:
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)

# --- Запуск бота ---
if __name__ == '__main__':
    logging.info("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)