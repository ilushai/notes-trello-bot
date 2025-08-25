from my_config import OPENAI_API_KEY
import requests

def speech_to_text(audio_path, language="ru"):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    files = {
        "file": open(audio_path, "rb"),
        "model": (None, "whisper-1"),
        "language": (None, language)
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    return response.json()["text"]
