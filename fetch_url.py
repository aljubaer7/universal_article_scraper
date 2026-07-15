import requests
from bs4 import BeautifulSoup
from seleniumbase import Driver
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
timeout = 10
# driver = Driver(uc=True, headless=True, page_load_strategy='eager')
# driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': 
#                     ['*.png', '*.jpg', '*.img', '*.jpeg', '*.gif', '*.webp', '*.mp4']})


class UrlFetcher:
    def __init__(self, url):
        self.url = url

    def getby_bs(self):
        session = requests.Session()
        session.headers.update(headers)
        try:
            response = session.get(self.url, timeout=timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")
                for tag in soup(avoid_tags):
                    tag.decompose()
                return soup
            else:
                return None
        except:
            return None

    # def getby_se(self):
    #     driver.uc_open(self.url)
    #     html_content = driver.page_source
    #     soup = BeautifulSoup(html_content, "lxml")
    #     for tag in soup(avoid_tags):
    #         tag.decompose()
    #     return soup

    # def get_soup(self):
    #     soup = self.getby_bs()
    #     if soup:
    #         if soup.title:
    #             return soup
    #     soup = self.getby_se()
    #     return soup
    
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