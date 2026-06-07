import asyncio
import os
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
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
PHONE = os.getenv("TELEGRAM_PHONE", "")
CHANNEL = "@tondev_news"
EMAIL_TO = "blackart2585@gmail.com"

# Ключевые слова для фильтрации
KEYWORDS = ["agent", "ai", "autonomous", "smart contract", "development", "tools"]

# OAuth2 scope для Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Получить авторизованный сервис Gmail через OAuth2"""
    creds = None
    
    # Проверяем сохранённые credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Если нет credentials или они истекли
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Первый раз — нужен файл credentials.json от Google
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Сохраняем credentials для следующего раза
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def send_email_via_gmail(subject, messages):
    """Отправить письмо через Gmail API"""
    try:
        service = get_gmail_service()
        
        # Форматируем сообщения
        email_body = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p>Найдено сообщений: {len(messages)}</p>
                <hr>
        """
        
        for msg in messages:
            email_body += f"""
                <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                    <p><strong>Время:</strong> {msg.date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Сообщение:</strong></p>
                    <p>{msg.text[:500]}...</p>
                    <p><a href="https://t.me/tondev_news/{msg.id}">Открыть в Telegram</a></p>
                </div>
            """
        
        email_body += """
                <hr>
                <p>Это автоматическое письмо от бота мониторинга TON Dev News</p>
            </body>
        </html>
        """
        
        # Создаём письмо
        message = MIMEText(email_body, 'html')
        message['to'] = EMAIL_TO
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw}
        
        # Отправляем
        service.users().messages().send(userId='me', body=send_message).execute()
        
        print(f"✅ Письмо отправлено ({len(messages)} сообщений)")
        return True
        
    except RefreshError:
        print("❌ Ошибка авторизации. Удали token.json и попробуй ещё раз")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки письма: {e}")
        return False

async def get_recent_messages(client, channel_name, hours=24):
    """Получает последние сообщения из канала"""
    entity = await client.get_entity(channel_name)
    messages = await client.get_messages(entity, limit=100)
    
    filtered_messages = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for message in messages:
        # Проверяем дату
        if message.date.replace(tzinfo=None) < cutoff_time:
            break
        
        # Проверяем наличие текста
        if not message.text:
            continue
        
        # Проверяем ключевые слова
        text_lower = message.text.lower()
        if any(keyword in text_lower for keyword in KEYWORDS):
            filtered_messages.append(message)
    
    return filtered_messages

async def main():
    """Основная функция"""
    client = TelegramClient("session_name", API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE)
        print("✅ Подключено к Telegram")
        
        # Получаем сообщения
        messages = await get_recent_messages(client, CHANNEL, hours=24)
        
        if messages:
            print(f"✅ Найдено {len(messages)} сообщений про AI-агенты на TON")
            
            subject = f"TON Dev News Мониторинг — {len(messages)} интересных постов"
            send_email_via_gmail(subject, messages)
        else:
            print("ℹ️ Интересных сообщений не найдено")
        
    except SessionPasswordNeededError:
        print("❌ Требуется пароль Telegram. Введите вручную.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
