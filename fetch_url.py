import requests
from bs4 import BeautifulSoup
import os
import sqlite3
conn = sqlite3.connect(r'data\metadata.db')
cursor = conn.cursor()

with open(r'data\headers.txt', 'r') as f:
    headers = eval(f.read())
avoid_tags = ['script', 'noscript', 'style', 'meta', 'link', 'aside', 'footer', 'img', 'cite', 'button', 'iframe', 'figcaption']


def fetch_url(url, timeout=10):
    session = requests.Session()
    session.headers.update(headers)
    try:
        response = session.get(url, timeout=timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "lxml")
            for tag in soup(avoid_tags):
                tag.decompose()
            return soup
        else:
            return None
    except:
        return None
    
def get_saved_soup(url):
    query = f"select file_name from url_html_encoded where url='{url}'"
    cursor.execute(query)
    file_name = cursor.fetchall()
    if file_name:
        file_name = file_name[0][0]
        path = r'saved soups'
        file_path = os.path.join(path, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'lxml')
        return soup
    else:
        return None