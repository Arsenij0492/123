import time
from datetime import datetime
import requests
from config import BOT_TOKEN, CHAT_ID, CATEGORIES, CHECK_INTERVAL
from database import Database
from parser import GameParser

class GameBot:
    def __init__(self):
        self.db = Database()
        self.parser = GameParser()
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.categories = CATEGORIES
    
    def send_telegram_message(self, text, image_url=None):
        """Отправляет сообщение в Telegram"""
        if image_url:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            payload = {
                'chat_id': self.chat_id,
                'caption': text,
                'photo': image_url,
                'parse_mode': 'HTML'
            }
        else:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def format_game_message(self, game_data):
        """Форматирует данные игры в красивое сообщение"""
        message = f"""<b>🎮 НОВАЯ ИГРА</b>

<b>{game_data['title']}</b>

📖 <i>{game_data['description']}</i>

🔗 <a href="{game_data['torrent_link']}">Скачать торрент</a>
💾 Размер: {game_data['size']}

<a href="{game_data['url']}">📌 Подробнее на сайте</a>"""
        return message
    
    def check_category(self, category_url):
        """Проверяет одну категорию на новые игры"""
        print(f"  📁 Проверка категории: {category_url}")
        
        game_links = self.parser.get_new_games_from_category(category_url)
        new_in_category = 0
        
        for link in game_links:
            if not self.db.is_game_sent(link):
                print(f"    🆕 Новая игра: {link[:80]}...")
                game_data = self.parser.parse_game_page(link)
                
                if game_data and game_data['torrent_link']:
                    message = self.format_game_message(game_data)
                    self.send_telegram_message(message, game_data['screenshot'])
                    self.db.mark_as_sent(link, game_data['title'])
                    new_in_category += 1
                    time.sleep(1)  # Не спамим Telegram API
        
        return new_in_category
    
    def check_all_categories(self):
        """Проверяет все категории на новые игры"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Проверка всех категорий...")
        print(f"📊 Всего категорий: {len(self.categories)}")
        
        total_new = 0
        
        for category in self.categories:
            try:
                new_count = self.check_category(category)
                total_new += new_count
                time.sleep(2)  # Пауза между категориями, чтобы не нагружать сайт
            except Exception as e:
                print(f"    ❌ Ошибка в категории {category}: {e}")
        
        if total_new == 0:
            print(f"✨ Новых игр не найдено")
        else:
            print(f"✅ Найдено и отправлено {total_new} новых игр!")
            stats = self.db.get_stats()
            print(f"📊 Всего отправлено игр за всё время: {stats}")
        
        return total_new
    
    def run(self):
        """Запуск бота с периодической проверкой"""
        print("=" * 60)
        print("🤖 Бот для мониторинга новых игр запущен")
        print("=" * 60)
        print(f"📡 Отслеживается категорий: {len(self.categories)}")
        print(f"⏱️  Интервал проверки: {CHECK_INTERVAL // 60} минут")
        print("=" * 60)
        print("Нажмите Ctrl+C для остановки\n")
        
        # Первый запуск — сразу проверяем
        self.check_all_categories()
        
        # Затем проверяем по расписанию
        while True:
            try:
                print(f"\n💤 Следующая проверка через {CHECK_INTERVAL // 60} минут")
                time.sleep(CHECK_INTERVAL)
                self.check_all_categories()
            except KeyboardInterrupt:
                print("\n🛑 Бот остановлен")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                print("🔄 Повторная попытка через 60 секунд...")
                time.sleep(60)

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН":
        print("❌ ОШИБКА: Укажите BOT_TOKEN в файле config.py")
        exit(1)
    
    bot = GameBot()
    bot.run()