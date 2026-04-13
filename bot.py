import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Читаем из аргументов командной строки
if len(sys.argv) >= 4:
    BOT_TOKEN = sys.argv[1]
    CHAT_ID = sys.argv[2]
    MONITOR_URL = sys.argv[3]
else:
    # Резервный вариант - из переменных окружения
    import os
    BOT_TOKEN = os.environ.get('8743041848:AAGl6YHMA1-ZLiQyfe3r7tvK9IyX-HAn1Qs')
    CHAT_ID = os.environ.get('1279775588')
    MONITOR_URL = os.environ.get('MONITOR_URL', 'https://stoigr.org/games-2026/')

print(f"[{datetime.now()}] Запуск проверки...")
print(f"BOT_TOKEN получен: {'ДА' if BOT_TOKEN else 'НЕТ'}")
print(f"CHAT_ID получен: {'ДА' if CHAT_ID else 'НЕТ'}")
print(f"MONITOR_URL: {MONITOR_URL}")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден")
    print(f"Аргументы: {sys.argv}")
    sys.exit(1)

if not CHAT_ID:
    print("❌ ОШИБКА: CHAT_ID не найден")
    sys.exit(1)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={
            'chat_id': CHAT_ID, 
            'text': text, 
            'parse_mode': 'HTML'
        }, timeout=10)
        print(f"  Ответ Telegram: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"  Ошибка отправки: {e}")
        return None

# Проверка работы бота
result = send_telegram(f"✅ Бот запущен в GitHub Actions!\nВремя: {datetime.now()}")

if result:
    print("✅ Сообщение отправлено успешно!")
else:
    print("❌ Не удалось отправить сообщение")

print(f"[{datetime.now()}] Проверка завершена")

def send_test_message():
    """Отправляет тестовое сообщение для проверки"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={
            'chat_id': CHAT_ID,
            'text': "✅ Бот работает и готов отправлять новые игры!",
            'parse_mode': 'HTML'
        }, timeout=10)
        print(f"Тестовое сообщение отправлено: {response.status_code}")
    except Exception as e:
        print(f"Ошибка отправки теста: {e}")

def main():
    send_test_message()  # Временная проверка
