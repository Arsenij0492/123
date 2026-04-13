import requests
import re
from bs4 import BeautifulSoup
from config import HEADERS, DESCRIPTION_LENGTH

class GameParser:
    def __init__(self):
        self.headers = HEADERS
    
    def get_new_games_from_category(self, category_url):
        """Получает список ссылок на новые игры со страницы категории"""
        try:
            response = requests.get(category_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'windows-1251'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            game_links = []
            
            # Ищем ссылки на игры
            articles = soup.find_all('article', class_='post')
            if not articles:
                # Если нет article, ищем по всем ссылкам
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    # Ссылки на игры обычно содержат /-games/ и .html
                    if href and '-games/' in href and href.endswith('.html'):
                        if 'page' not in href and '#' not in href:
                            if not href.startswith('http'):
                                href = 'https://stoigr.org' + href
                            game_links.append(href)
            
            # Убираем дубликаты
            seen = set()
            unique_links = []
            for link in game_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            return unique_links[:5]  # Не больше 20 за раз
            
        except Exception as e:
            print(f"Ошибка при получении списка игр: {e}")
            return []
    
    def parse_game_page(self, game_url):
        """Парсит страницу игры и возвращает словарь с данными"""
        try:
            response = requests.get(game_url, headers=self.headers, timeout=10)
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
            
            return {
                'title': title,
                'description': description,
                'torrent_link': torrent_link,
                'size': size,
                'screenshot': screenshot,
                'url': game_url
            }
            
        except Exception as e:
            print(f"Ошибка при парсинге {game_url}: {e}")
            return None