# bot.py
# ... (все импорты и код до функции process_note остаются прежними)

# Импортируем ADMIN_ID из конфига
from user_config import AUTHORIZED_USERS, ADMIN_USERNAME, ADMIN_ID

# ... (остальной код до функции process_note)

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
        reply_message = "✅ Записал в Google Sheets."
        
        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ: Проверяем, является ли пользователь админом ---
        if message.from_user.id == ADMIN_ID:
            # Если это админ, пробуем создать карточку в Trello
            trello_success = create_trello_card(text)
            if trello_success:
                reply_message = "✅ Записал в Google Sheets и создал карточку в Trello!"
        
        await message.reply(reply_message)
    else:
        await message.reply("❌ **Ошибка при записи в Google Sheets!**\n\nПроверь, что:\n1. Ссылка на таблицу верная.\n2. Ты дал права редактора моему сервисному email.")

# ... (весь остальной код после process_note остается без изменений)