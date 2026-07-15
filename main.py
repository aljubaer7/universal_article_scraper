import random
from datetime import datetime

import fetch_url
import collect_urls
import processor as pr


    ## get base-urls
with open(r'data\base_urls.txt', 'r') as f:
    base_urls = [item.strip() for item in f]
print(f'{len(base_urls)} base-urls found.')

# collect first-level urls
ic = 0
first_level_urls = []
for url in base_urls:
    fetcher = fetch_url.UrlFetcher(url)
    soup = fetcher.get_soup()
    if soup:
        collector = collect_urls.CollectUrls()
        fl_urls = collector.get_flurl(url, soup)
        first_level_urls.extend(fl_urls)
    ic += 1
    print(f'\rFetching ground-zero urls - {ic}/{len(base_urls)}', end='')
with open(r'data\first_level_urls.txt', 'w', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in first_level_urls)
print(f'\n{len(first_level_urls)} first-level urls saved successfully.')

 ## collect second-level urls
collector = collect_urls.CollectUrls() # remove

with open(r'data\first_level_urls.txt', 'r') as f:
    first_level_urls = [item.strip() for item in f]
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(first_level_urls)} first-level urls found.')
random.shuffle(first_level_urls)

ic = 0
sec_level_url = []
for url in first_level_urls:
    fetcher = fetch_url.UrlFetcher(url)
    soup = fetcher.getby_bs()
    if soup:
        sl_urls = collector.get_slurl(url, soup)
        if sl_urls:
            for item in sl_urls:
                tail = '/'.join(item.split('/')[4:])
                if 'article' in tail or tail.count('-') > 3:
                    sec_level_url.append(item)
    ic += 1
    print(f'\r{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Fetching second-level urls - {ic}/{len(first_level_urls)}', end='')
sec_level_url = [item for item in sec_level_url if item not in first_level_urls]
with open(r'data\second_level_urls.txt', 'w', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in sec_level_url)
print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} second-level urls saved successfully.')

 ## text collector
txt_file = r'data\corpus.txt'
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

with open(r'data\old_level_2_urls.txt', 'r') as f:
    sec_level_url = [item.strip() for item in f]
# check visited urls
with open(r'data\visited_urls.txt', 'r', encoding='utf-8') as f:
    visited_urls = [item.strip() for item in f]
sec_level_url = [url for url in sec_level_url if url not in visited_urls]
random.shuffle(sec_level_url)
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} unique urls found!')




# Loop urls
ic = 0
error = 0
visited = 0

for url in sec_level_url[0:100]:
    # fetcher = fetch_url.UrlFetcher(url)
    soup = fetch_url.get_saved_soup(url)
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
        

    if error == 4:
        print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  4 consecutive errors!!')
        break
    ic += 1
    print(f'\r{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {ic}/{len(sec_level_url)}', end='')

