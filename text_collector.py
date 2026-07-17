import random
import pandas as pd
from datetime import datetime

import fetch_url
import processor as pr

# output text-file name
txt_file = r'data\corpus_a.txt'

# tags and parameters
tags = ['div', 'span', 'article', 'section']
parameters = {
    'min_text_lines': 4,
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
with open(r'data\second_level_urls.txt', 'r', encoding='utf-8') as f:
    sec_level_url = [item.strip() for item in f]
random.shuffle(sec_level_url)

df = pd.DataFrame({'urls': sec_level_url})
df = df.drop_duplicates(subset='urls')
# exclude visited urls
with open(r'data\visited_urls.txt', 'r', encoding='utf-8') as f:
    visited_urls = [item.strip() for item in f]
df = df[~df['urls'].isin(visited_urls)]
sec_level_url = df['urls'].to_list()
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} unique urls found!')


# main loop
ic = 0
error = 0

for url in sec_level_url:
    fetcher = fetch_url.UrlFetcher(url)
    soup = fetcher.getby_bs()
    if soup == None:
        error += 1
    else:
        error = 0
        if soup.title:
            # main process----------------------------------------------------/
            title = soup.title.text.strip().split('|')[0].strip()
            article = pr.SearchByArticle(soup)
            text_lines, df = article.get_article_text()
            if text_lines:
                pr.save_text(url, title, text_lines, df, txt_file, sql=True)
            else:
                text = pr.SearchByAttributes(soup, tags, parameters)
                text_lines, df = text.loop_attributes()
                if text_lines:
                    pr.save_text(url, title, text_lines, df, txt_file, sql=True)
                # end process----------------------------------------------------/
                with open(r'data\visited_urls.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}\n')
    if error == 5:
        print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  5 consecutive errors!!')
        break
    ic += 1
    print(f'\r{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Visiting urls {ic}/{len(sec_level_url)}', end='')