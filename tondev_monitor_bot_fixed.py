import asyncio
import os
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from dotenv import load_dotenv

load_dotenv()

# Конфиг
API_ID = int(os.getenv("TELEGRAM_API_ID", ""))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
EMAIL_TO = "blackart2585@gmail.com"

# Каналы для мониторинга
CHANNELS = [
    "@Openai_U",
    "@thirtythreestables",
    "@tondev_news",
    "@tonstatus",
    "@telepeng",
]

# Ключевые слова для фильтрации
KEYWORDS = ["agent", "ai", "autonomous", "smart contract", "development", "tools"]

# OAuth2 scope для Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_email_via_gmail(subject, messages_by_channel):
    try:
        service = get_gmail_service()

        total = sum(len(msgs) for msgs in messages_by_channel.values())

        email_body = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p>Найдено сообщений: {total}</p>
                <hr>
        """

        for channel, messages in messages_by_channel.items():
            if not messages:
                continue
            email_body += f"<h3>📢 {channel} — {len(messages)} постов</h3>"
            for msg in messages:
                channel_name = channel.replace("@", "")
                email_body += f"""
                <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                    <p><strong>Время:</strong> {msg.date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Сообщение:</strong></p>
                    <p>{msg.text[:500]}...</p>
                    <p><a href="https://t.me/{channel_name}/{msg.id}">Открыть в Telegram</a></p>
                </div>
                """

        email_body += """
                <hr>
                <p>Это автоматическое письмо от бота мониторинга</p>
            </body>
        </html>
        """

        message = MIMEText(email_body, 'html')
        message['to'] = EMAIL_TO
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw}).execute()

        print(f"✅ Письмо отправлено ({total} сообщений из {len(messages_by_channel)} каналов)")
        return True

    except RefreshError:
        print("❌ Ошибка авторизации Gmail. Удали token.json и попробуй ещё раз")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки письма: {e}")
        return False

async def get_recent_messages(client, channel_name, hours=24):
    try:
        entity = await client.get_entity(channel_name)
        messages = await client.get_messages(entity, limit=100)

        filtered_messages = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for message in messages:
            if message.date.replace(tzinfo=None) < cutoff_time:
                break
            if not message.text:
                continue
            text_lower = message.text.lower()
            if any(keyword in text_lower for keyword in KEYWORDS):
                filtered_messages.append(message)

        print(f"  📌 {channel_name}: найдено {len(filtered_messages)} постов")
        return filtered_messages

    except Exception as e:
        print(f"  ❌ {channel_name}: ошибка — {e}")
        return []

async def main():
    if not SESSION_STRING:
        print("❌ ОШИБКА: SESSION_STRING не установлен!")
        print("Запусти setup_session.py локально чтобы получить session string")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        print("✅ Подключено к Telegram")

        if not await client.is_user_authorized():
            print("❌ ОШИБКА: Сессия невалидна!")
            print("Запусти setup_session.py локально чтобы обновить session string")
            return

        print(f"\n🔍 Проверяю {len(CHANNELS)} каналов...\n")

        messages_by_channel = {}
        for channel in CHANNELS:
            messages = await get_recent_messages(client, channel, hours=24)
            messages_by_channel[channel] = messages

        total = sum(len(msgs) for msgs in messages_by_channel.values())

        if total > 0:
            print(f"\n✅ Найдено {total} интересных постов")
            subject = f"Мониторинг каналов — {total} интересных постов за 24ч"
            send_email_via_gmail(subject, messages_by_channel)
        else:
            print("\nℹ️ Интересных сообщений не найдено")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 Запускаю мониторинг каналов...")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    asyncio.run(main())
