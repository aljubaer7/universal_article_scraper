import random
import pandas as pd
from datetime import datetime

import processor as pr
import fetch_url
fetcher = fetch_url.UrlFetcher()

# output text-file name
txt_file = r'data\corpus_b.txt'

# tags and parameters
tags = ['div', 'span', 'article', 'section']
parameters = {
    'min_text_lines': 6,
    'avg_line_len': 100,
    'min_text_length': 1000,
    'max_line_len_p': 40,
    'max_tdot': 3,
    'max_colon': 12,
    'max_int_txt_simi': 0.95,
    'max_exr_txt_simi': 0.998,
    'min_sent_score': 0.60
}

# load urls
sec_level_url = open(r'data\second_level_urls.txt', 'r', encoding='utf-8').read().split()
l = len(sec_level_url)
random.shuffle(sec_level_url)

df = pd.DataFrame({'urls': sec_level_url})
df = df.drop_duplicates(subset='urls')
# exclude visited urls
visited_urls = open(r'data\visited_urls.txt', 'r', encoding='utf-8').read().split()
df = df[~df['urls'].isin(visited_urls)]
sec_level_url = df['urls'].to_list()
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} unique urls ({l}) found!')


# main loop
ic = 0
error = 0
visited = 0

for url in sec_level_url:
    soup = fetcher.getbybs(url)
    if soup.status_code.text != '200':
        error += 1
    else:
        error = 0
        if soup.title:
            # main process----------------------------------------------------/
            title = soup.title.text.strip().split('|')[0].strip()
            article = pr.SearchByArticle(soup, parameters=parameters)
            text_lines, df = article.get_article_text()
            if text_lines:
                pr.save_text(url, title, text_lines, df, txt_file)
            else:
                text = pr.SearchByAttributes(soup, tags, parameters=parameters)
                text_lines, df = text.loop_attributes()
                if text_lines:
                    pr.save_text(url, title, text_lines, df, txt_file)
                # end process----------------------------------------------------/
                visited += 1

        with open(r'data\visited_urls.txt', 'a', encoding='utf-8') as f:
            f.write(f'{url}\n')
                
    if error == 5:
        print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  5 consecutive errors!!')
        break
    ic += 1
    print(f'\r{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Visiting urls {ic}/{len(sec_level_url)}. Success rate {round((visited/ic)*100, 1)}%', end='')