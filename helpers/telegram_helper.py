import os

import requests

from dotenv import load_dotenv


class TelegramHelper:
    """
    Class for sending messages via Telegram API.
    """

    load_dotenv()

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message):
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Error: timeout request")
            return None
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to Telegram: {e}")
            return None
