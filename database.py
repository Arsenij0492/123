import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file='games.db'):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        """Создаёт таблицу, если её нет"""
        conn = sqlite3.connect(self.db_file)
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
        print(f"✅ База данных готова: {self.db_file}")
    
    def is_game_sent(self, url):
        """Проверяет, отправляли ли уже эту игру"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT 1 FROM sent_games WHERE url = ?", (url,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def mark_as_sent(self, url, title):
        """Отмечает игру как отправленную"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO sent_games (url, title, sent_time) VALUES (?, ?, ?)",
            (url, title, datetime.now())
        )
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Возвращает статистику"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sent_games")
        count = c.fetchone()[0]
        conn.close()
        return count
