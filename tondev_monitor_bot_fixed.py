import asyncio
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

# Конфиг
API_ID = int(os.getenv("TELEGRAM_API_ID", ""))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY", "")
EMAIL_FROM = "blackart2585@gmail.com"
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
KEYWORDS = ["agent", "ai", "autonomous", "tools", "library", "blueprint", "sdk", "update", "release", "new", "ton", "tvm", "smart contract", "developer"]


def send_email(subject, messages_by_channel):
    try:
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
                    <p>{msg.text[:500]}</p>
                    <p><a href="https://t.me/{channel_name}/{msg.id}">Открыть в Telegram</a></p>
                </div>
                """

        email_body += """
                <hr>
                <p>Автоматическое письмо от бота мониторинга TON каналов</p>
            </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=15) as server:
            server.starttls()
            server.login(EMAIL_FROM, BREVO_SMTP_KEY)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        print(f"✅ Письмо отправлено через Brevo ({total} сообщений)")
        return True

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
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        print("✅ Подключено к Telegram")

        if not await client.is_user_authorized():
            print("❌ ОШИБКА: Сессия невалидна!")
            return

        print(f"\n🔍 Проверяю {len(CHANNELS)} каналов...\n")

        messages_by_channel = {}
        for channel in CHANNELS:
            messages = await get_recent_messages(client, channel, hours=24)
            messages_by_channel[channel] = messages

        total = sum(len(msgs) for msgs in messages_by_channel.values())

        if total > 0:
            print(f"\n✅ Найдено {total} интересных постов")
            subject = f"Мониторинг TON каналов — {total} постов за 24ч"
            send_email(subject, messages_by_channel)
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
