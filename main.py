# services/speech_to_text.py
import openai
from my_config import OPENAI_API_KEY

# Убедитесь, что ваш OpenAI клиент инициализирован с API ключом
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def speech_to_text(audio_file_path: str) -> str:
    """
    Преобразует аудиофайл в текст с помощью OpenAI Whisper.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Ошибка при распознавании речи: {e}")
        return "Не удалось распознать речь."