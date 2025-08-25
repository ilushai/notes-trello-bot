# services/trello_service.py
import requests
import logging
from my_config import TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID, TRELLO_LABEL_ID

def create_trello_card(name: str):
    """
    Создает карточку в Trello, если в конфиге указаны все необходимые данные.
    """
    # Проверяем, что все ключи Trello заполнены. Если нет - выходим.
    if not all([TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID, TRELLO_LABEL_ID]):
        logging.info("Ключи для Trello не настроены. Пропускаю создание карточки.")
        return False

    url = "https://api.trello.com/1/cards"
    
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'idList': TRELLO_LIST_ID,
        'name': name,
        'idLabels': TRELLO_LABEL_ID
    }

    try:
        response = requests.post(url, params=query)
        response.raise_for_status()  # Проверка на ошибки HTTP (4xx или 5xx)
        logging.info(f"Карточка Trello '{name}' успешно создана.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при создании карточки Trello: {e}")
        return False