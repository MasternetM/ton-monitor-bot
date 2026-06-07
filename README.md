# TON Dev News Мониторинг Бот

Бот читает канал @tondev_news, ловит посты про AI-агенты на TON и отправляет интересные на почту.

## Установка

### 1. Получить Telegram API credentials

1. Перейти на https://my.telegram.org
2. Залогиниться с номером телефона
3. Создать новое приложение
4. Получить `API_ID` и `API_HASH`

### 2. Настроить Gmail

1. Включить 2FA в Google Account
2. Создать App Password: https://myaccount.google.com/apppasswords
3. Скопировать пароль (16 символов)

### 3. Клонировать и настроить

```bash
git clone <repo>
cd tondev-monitor
pip install -r requirements.txt
cp .env.example .env
```

### 4. Заполнить .env

```
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+1234567890
EMAIL_USER=blackart2585@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
```

### 5. Запустить локально

```bash
python tondev_monitor_bot.py
```

При первом запуске потребуется подтверждение кода из Telegram.

## Развёртывание на Railway

1. Создать проект на https://railway.app
2. Подключить GitHub репозиторий
3. Добавить переменные окружения (из .env)
4. Добавить Procfile:

```
worker: python tondev_monitor_bot.py
```

5. Создать scheduled job для запуска в 8:00 UTC

## Как это работает

- Ежедневно в 8:00 проверяет канал @tondev_news
- Ищет сообщения содержащие: agent, ai, autonomous, smart contract, development, tools
- Отправляет найденные на почту blackart2585@gmail.com
- Ссылки на посты кликабельны в письме

## Ключевые слова

Если нужно изменить фильтры — отредактируй:
```python
KEYWORDS = ["agent", "ai", "autonomous", "smart contract", "development", "tools"]
```

## Логирование

Логи выводятся в консоль. На Railway они видны в Dashboard > Logs.

## TODO

- [ ] Добавить более умные фильтры (не только ключевые слова)
- [ ] Сохранять историю проверенных сообщений
- [ ] Добавить несколько каналов для мониторинга
