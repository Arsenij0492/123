import os
import sys
from datetime import datetime
import requests
from database import Database
from parser import GameParser

# Настройки из переменных окружения (будут в GitHub Secrets)
BOT_TOKEN = os.getenv('8743041848:AAGl6YHMA1-ZLiQyfe3r7tvK9IyX-HAn1Qs')
CHAT_ID = os.getenv('1279775588')
MONITOR_URL = os.getenv('MONITOR_URL', 'https://stoigr.org/games-2026/')

def send_telegram_message(text, image_url=None):
    """Отправляет сообщение в Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Ошибка: BOT_TOKEN или CHAT_ID не заданы")
        return None
    
    if image_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': CHAT_ID,
            'caption': text,
            'photo': image_url,
            'parse_mode': 'HTML'
        }
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return None

def format_game_message(game_data):
    """Форматирует данные игры в красивое сообщение"""
    message = f"""<b>🎮 НОВАЯ ИГРА</b>

<b>{game_data['title']}</b>

📖 <i>{game_data['description']}</i>

🔗 <a href="{game_data['torrent_link']}">Скачать торрент</a>
💾 Размер: {game_data['size']}

<a href="{game_data['url']}">📌 Подробнее на сайте</a>"""
    return message

def main():
    """Одноразовая проверка новых игр"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запуск проверки...")
    
    # Проверяем настройки
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не задан в переменных окружения")
        sys.exit(1)
    
    if not CHAT_ID:
        print("❌ Ошибка: CHAT_ID не задан в переменных окружения")
        sys.exit(1)
    
    db = Database()
    parser = GameParser()
    
    # Получаем список игр
    game_links = parser.get_new_games_from_category(MONITOR_URL)
    print(f"Найдено ссылок на игры: {len(game_links)}")
    
    new_games_found = 0
    
    for link in game_links[:10]:  # Не больше 10 игр за раз
        if not db.is_game_sent(link):
            print(f"  🆕 Новая игра: {link[:80]}...")
            game_data = parser.parse_game_page(link)
            
            if game_data and game_data['torrent_link']:
                message = format_game_message(game_data)
                send_telegram_message(message, game_data['screenshot'])
                db.mark_as_sent(link, game_data['title'])
                new_games_found += 1
    
    if new_games_found == 0:
        print("✨ Новых игр не найдено")
    else:
        print(f"✅ Отправлено {new_games_found} новых игр")
        stats = db.get_stats()
        print(f"📊 Всего отправлено игр за всё время: {stats}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка завершена")

if __name__ == "__main__":
    main()
