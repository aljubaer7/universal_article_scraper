import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


import os
import pandas as pd
import uuid

import sqlite3
conn = sqlite3.connect(r'data\metadata.db')
cursor = conn.cursor()

with open(r'data\headers.txt', 'r') as f:
    headers = eval(f.read())
avoid_tags = ['script', 'noscript', 'style', 'meta', 'link', 'aside', 'footer', 
              'img', 'figure', 'audio', 'video', 'cite', 'button', 'iframe', 'figcaption', 'svg', 'path', 'source']


class UrlFetcher:
    def __init__(self, timeout: int = 7, fallback: bool = False):
        self.fallback = fallback
        self.timeout = timeout
        
        if self.fallback:
            # create driver options
            options = Options()
            # 1. Set page load strategy to 'eager' (don't wait for images/resources)
            options.page_load_strategy = 'none'  # or 'none' for even faster
            # 10. Headless mode (faster if you don't need GUI)
            options.add_argument('--headless=new')
            # 2. Disable images
            options.add_argument('--blink-settings=imagesEnabled=false')           
            # 3. Disable JavaScript (optional - can break some sites but speeds up)
            # options.add_argument('--disable-javascript')
            # 4. Disable GPU and hardware acceleration
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            # 5. Memory and performance optimizations
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--no-sandbox')
            # 6. Disable extensions and popups
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-geolocation')
            # 7. Disable features that slow down loading
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            # 8. Disable various resource types
            options.add_argument('--disable-webgl')
            options.add_argument('--disable-pepper-3d')
            options.add_argument('--disable-accelerated-2d-canvas')
            options.add_argument('--disable-accelerated-jpeg-decoding')
            options.add_argument('--disable-accelerated-mjpeg-decode')
            options.add_argument('--disable-accelerated-video-decode')
            # 9. Reduce memory usage
            options.add_argument('--max_old_space_size=512')
            # 11. Disable logging and metrics
            options.add_argument('--log-level=3')
            options.add_argument('--silent')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # 12. Block specific resource types via experimental options
            prefs = {
                # Disable images
                'profile.managed_default_content_settings.images': 2,
                # Disable plugins (Flash, etc.)
                'profile.managed_default_content_settings.plugins': 2,
                # Disable notifications
                'profile.managed_default_content_settings.notifications': 2,
                # Disable autoplay
                'profile.managed_default_content_settings.media_stream': 2,
                # Disable geolocation
                'profile.managed_default_content_settings.geolocation': 2,
            }
            options.add_experimental_option('prefs', prefs)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(7)
            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {
                        'urls': [
                            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.avif', '*.svg', '*.ico',
                            '*.mp4', '*.webm', '*.avi', '*.mov', '*.mkv',
                            '*.mp3', '*.wav', '*.ogg', '*.flac',
                            '*.woff', '*.woff2', '*.ttf', '*.otf', '*.eot', '*.json', '*.xml'
                            # '*.css',
                            ]})


    def getbybs(self, url: str):
        session = requests.Session()
        session.headers.update(headers)
        try:
            response = session.get(url, timeout=self.timeout) # out
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")
                for tag in soup(avoid_tags):
                    tag.decompose()
                # add status_code
                status_tag = soup.new_tag('status_code')
                status_tag.string = str(response.status_code)
                soup.append(status_tag)
                return soup
            else:
                return BeautifulSoup(f'<status_code>{response.status_code}</status_code>', 'html.parser')
        except Exception as e:
            return BeautifulSoup(f'<status_code>11001</status_code><status>{e}</status>', 'html.parser')
            
    def getbyse(self, url: str):
        try:
            self.driver.get(url)
            time.sleep(3)
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, "lxml")
            for tag in soup(avoid_tags):
                tag.decompose()
            return soup
        except Exception as e:
            return BeautifulSoup(f'<status_code>{e}</status_code>', 'html.parser')

    def get_soup(self, url:str):
        soup = self.getbybs(url)
        if int(soup.status_code.text) != 200 and self.fallback:
            soup = self.getbyse(url)
            return soup
        else:
            return soup

    
def save_soup(soup, url):
    file_name = f'{uuid.uuid4().hex}.html'
    path = r'C:\Users\Juve\Documents\dataset_builder\saved_soups'
    file_path = os.path.join(path, file_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
    df = pd.DataFrame([{'url': url, 'file_name': file_name}])
    df.to_sql('saved_soup', conn, if_exists='append', index=False)
    conn.commit()
    
def get_saved_soup(url):
    query = f"select file_name from saved_soup where url='{url}'"
    cursor.execute(query)
    file_name = cursor.fetchall()
    if file_name:
        file_name = file_name[0][0]
        path = r'saved_soups'
        file_path = os.path.join(path, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'lxml')
        return soup
    else:
        return None