import os
import sys
import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import re

# ========== НАСТРОЙКИ ==========
# Читаем из аргументов командной строки или переменных окружения
if len(sys.argv) >= 4:
    BOT_TOKEN = sys.argv[1]
    CHAT_ID = sys.argv[2]
    MONITOR_URL = sys.argv[3]
else:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    CHAT_ID = os.environ.get('CHAT_ID')
    MONITOR_URL = os.environ.get('MONITOR_URL', 'https://stoigr.org/games-2026/')

# Настройки
DESCRIPTION_LENGTH = 150
MAX_GAMES_PER_RUN = 5  # Не больше 5 игр за раз

# ========== БАЗА ДАННЫХ ==========
def init_db():
    """Создаёт таблицу, если её нет"""
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sent_games (
            url TEXT PRIMARY KEY,
            title TEXT,
            sent_time TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_game_sent(url):
    """Проверяет, отправляли ли уже эту игру"""
    try:
        conn = sqlite3.connect('games.db')
        c = conn.cursor()
        c.execute("SELECT 1 FROM sent_games WHERE url = ?", (url,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def mark_as_sent(url, title):
    """Отмечает игру как отправленную"""
    try:
        conn = sqlite3.connect('games.db')
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO sent_games (url, title, sent_time) VALUES (?, ?, ?)",
            (url, title, datetime.now())
        )
        conn.commit()
        conn.close()
        print(f"  💾 Сохранено в БД: {title[:50]}...")
    except Exception as e:
        print(f"  ❌ Ошибка сохранения: {e}")

def get_stats():
    """Возвращает статистику"""
    try:
        conn = sqlite3.connect('games.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sent_games")
        count = c.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# ========== TELEGRAM ==========
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
        print(f"  📨 Отправлено в Telegram: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"  ❌ Ошибка отправки в Telegram: {e}")
        return None

# ========== ПАРСИНГ ==========
def get_game_links_from_category():
    """Получает список ссылок на игры со страницы категории"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(MONITOR_URL, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'windows-1251'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        game_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '-games/' in href and href.endswith('.html'):
                if 'page' not in href and '#' not in href:
                    if not href.startswith('http'):
                        href = 'https://stoigr.org' + href
                    if href not in game_links:
                        game_links.append(href)
        
        # Убираем дубликаты и ограничиваем количество
        seen = set()
        unique_links = []
        for link in game_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links[:MAX_GAMES_PER_RUN]
        
    except Exception as e:
        print(f"  ❌ Ошибка при получении списка игр: {e}")
        return []

def parse_game_page(game_url):
    """Парсит страницу игры и возвращает словарь с данными"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(game_url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'windows-1251'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Название игры
        title_tag = soup.find('h1', class_='title')
        if not title_tag:
            title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Неизвестная игра"
        
        # Описание (первые N символов)
        desc_div = soup.find('div', class_='post-cont')
        description = ""
        if desc_div:
            first_p = desc_div.find('p')
            if first_p:
                text = first_p.get_text(strip=True)
                text = re.sub(r'\s+', ' ', text)
                if len(text) > DESCRIPTION_LENGTH:
                    description = text[:DESCRIPTION_LENGTH] + "..."
                else:
                    description = text
        
        # Ссылка на торрент
        torrent_link = None
        download_btn = soup.find('a', class_='button4')
        if download_btn and download_btn.get('href'):
            torrent_link = download_btn.get('href')
        
        # Размер игры
        size = "Неизвестно"
        size_elem = soup.find('center', string=re.compile(r'Размер:'))
        if size_elem:
            size_text = size_elem.get_text(strip=True)
            size = size_text.replace('Размер:', '').strip()
        
        # Скриншот (первый)
        screenshot = None
        screen_div = soup.find('div', id='screen')
        if screen_div:
            first_img = screen_div.find('img')
            if first_img and first_img.get('src'):
                screenshot = first_img.get('src')
                if not screenshot.startswith('http'):
                    screenshot = 'https://stoigr.org' + screenshot
        
        # Год выхода (для фильтрации)
        year = None
        info_items = soup.find_all('li', class_=['first', 'second'])
        for item in info_items:
            if 'Год выхода:' in item.get_text():
                year_match = re.search(r'(\d{4})', item.get_text())
                if year_match:
                    year = int(year_match.group(1))
                break
        
        return {
            'title': title,
            'description': description,
            'torrent_link': torrent_link,
            'size': size,
            'screenshot': screenshot,
            'url': game_url,
            'year': year
        }
        
    except Exception as e:
        print(f"  ❌ Ошибка при парсинге {game_url}: {e}")
        return None

# ========== ФОРМАТИРОВАНИЕ СООБЩЕНИЯ ==========
def format_game_message(game_data):
    """Форматирует данные игры в красивое сообщение"""
    message = f"""<b>🎮 НОВАЯ ИГРА</b>

<b>{game_data['title']}</b>

📖 <i>{game_data['description']}</i>

🔗 <a href="{game_data['torrent_link']}">Скачать торрент</a>
💾 Размер: {game_data['size']}

<a href="{game_data['url']}">📌 Подробнее на сайте</a>"""
    return message

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Одноразовая проверка новых игр с heartbeat"""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запуск проверки...")
    print(f"BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
    print(f"CHAT_ID: {'✅ Есть' if CHAT_ID else '❌ НЕТ'}")
    print(f"MONITOR_URL: {MONITOR_URL}")
    print(f"MAX_GAMES_PER_RUN: {MAX_GAMES_PER_RUN}")
    
    # Проверка обязательных настроек
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не задан")
        sys.exit(1)
    
    if not CHAT_ID:
        print("❌ Ошибка: CHAT_ID не задан")
        sys.exit(1)
    
    # Инициализируем базу данных
    init_db()
    stats = get_stats()
    print(f"📊 В базе данных: {stats} игр")
    
    # Heartbeat сообщение (отправляем всегда, чтобы знать что бот жив)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    heartbeat_msg = f"🟢 <b>Мониторинг игр активен</b>\n\n⏰ Время: {current_time}\n📡 Категория: {MONITOR_URL.split('/')[-2] if MONITOR_URL.endswith('/') else MONITOR_URL.split('/')[-1]}\n📊 Отправлено игр всего: {stats}\n⏱️ Проверка: каждые 30 минут"
    
    # Получаем список игр
    game_links = get_game_links_from_category()
    print(f"🔍 Найдено ссылок на игры: {len(game_links)}")
    
    new_games_found = 0
    new_games_titles = []
    
    for link in game_links:
        if not is_game_sent(link):
            print(f"  🆕 Новая игра: {link[:80]}...")
            game_data = parse_game_page(link)
            
            if game_data and game_data['torrent_link']:
                # Отправляем только игры текущего года или без года
                current_year = datetime.now().year
                if game_data.get('year') is None or game_data['year'] >= current_year - 1:
                    message = format_game_message(game_data)
                    send_telegram_message(message, game_data['screenshot'])
                    mark_as_sent(link, game_data['title'])
                    new_games_found += 1
                    new_games_titles.append(game_data['title'])
                else:
                    print(f"  ⏭️ Пропущена старая игра: {game_data['title']} ({game_data.get('year', '?')})")
                    mark_as_sent(link, game_data['title'])  # Помечаем как отправленную, но не шлём
            elif game_data:
                # Если нет торрент-ссылки, просто помечаем как отправленную
                mark_as_sent(link, game_data['title'])
                print(f"  ⏭️ Пропущена (нет торрента): {game_data['title']}")
    
    # Отправляем итоговое сообщение
    if new_games_found > 0:
        # Если есть новые игры, отправляем резюме
        games_list = "\n".join([f"  • {title}" for title in new_games_titles[:5]])
        summary = f"✅ <b>Найдено {new_games_found} новых игр!</b>\n\n{games_list}"
        if new_games_found > 5:
            summary += f"\n  • и ещё {new_games_found - 5}..."
        send_telegram_message(summary)
    else:
        # Если новых игр нет, отправляем heartbeat
        send_telegram_message(heartbeat_msg + "\n\n✨ Новых игр не найдено")
    
    # Финальная статистика
    new_stats = get_stats()
    print(f"✅ Отправлено новых игр: {new_games_found}")
    print(f"📊 Всего в базе: {new_stats} игр")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка завершена")
    print("=" * 50)

if __name__ == "__main__":
    main()
