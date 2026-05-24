import requests
import logging
from .config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID

logger = logging.getLogger(__name__)


class LineSender:
    """LINE Messaging API でメッセージを送信"""

    API_URL = "https://api.line.me/v2/bot/message/push"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    @staticmethod
    def send_message(message_content) -> bool:
        """
        メッセージを送信（テキスト or フレックスメッセージ）
        返り値: 成功時 True、失敗時 False
        """
        if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
            logger.error("LINE_CHANNEL_ACCESS_TOKEN or LINE_USER_ID is not set")
            return False

        # message_content が文字列の場合はテキストメッセージに、辞書の場合はそのまま使用
        if isinstance(message_content, str):
            messages = [{"type": "text", "text": message_content}]
        else:
            messages = [message_content]

        payload = {
            "to": LINE_USER_ID,
            "messages": messages
        }

        try:
            response = requests.post(
                LineSender.API_URL,
                json=payload,
                headers=LineSender.HEADERS,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Message sent successfully to LINE")
                return True
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"Error sending message to LINE: {e}")
            return False

    @staticmethod
    def send_notification(title: str, message: str) -> bool:
        """エラー通知用メッセージを送信"""
        full_message = f"⚠️ {title}\n\n{message}"
        return LineSender.send_message(full_message)
