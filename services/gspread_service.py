# services/gspread_service.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from threading import Lock
import os

# --- АБСОЛЮТНЫЙ ПУТЬ К ФАЙЛУ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(os.path.dirname(BASE_DIR), 'credentials.json')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
gs_lock = Lock()

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_sheet_by_url(spreadsheet_url: str):
    """Подключается к Google Sheets и возвращает рабочий лист по ссылке."""
    try:
        logging.info(f"Использую файл учетных данных: {CREDENTIALS_FILE}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ: Открываем по ссылке ---
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet.sheet1
    except FileNotFoundError:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: Файл credentials.json не найден по пути: {CREDENTIALS_FILE}")
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"Таблица по указанной ссылке не найдена. Убедитесь, что ссылка верна.")
        return None
    except Exception as e:
        logging.error(f"Ошибка при подключении к Google Sheets: {e}")
        return None

def add_note_to_sheet(text: str, spreadsheet_url: str):
    """Добавляет текстовую заметку в Google Таблицу, указанную по ссылке."""
    with gs_lock:
        logging.info(f"Попытка подключения к Google Таблице по ссылке...")
        sheet = get_sheet_by_url(spreadsheet_url)
        if sheet:
            try:
                logging.info(f"Подключение успешно. Добавляю заметку: '{text}'")
                list_of_values = sheet.col_values(1)
                next_row = len(list_of_values) + 1
                sheet.update_cell(next_row, 1, text)
                logging.info(f"Заметка успешно сохранена в строке {next_row}.")
                return True
            except Exception as e:
                logging.error(f"Не удалось записать данные в таблицу: {e}")
                return False
        else:
            logging.error("Не удалось получить доступ к рабочему листу.")
            return False

def get_service_account_email():
    """Возвращает email сервисного аккаунта из credentials.json для инструкций."""
    try:
        logging.info(f"Пытаюсь прочитать email из файла: {CREDENTIALS_FILE}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        email = creds.service_account_email
        logging.info(f"Email успешно прочитан: {email}")
        return email
    except FileNotFoundError:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: Файл credentials.json не найден по пути: {CREDENTIALS_FILE}")
        return None
    except Exception as e:
        logging.error(f"Не удалось прочитать email из файла credentials.json. Ошибка: {e}")
        return None