import random
from datetime import datetime

import fetch_url
fetcher = fetch_url.UrlFetcher()
import collect_urls
collector = collect_urls.CollectUrls()

with open(r'data\first_level_urls.txt', 'r') as f:
    first_level_urls = [item.strip() for item in f]
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(first_level_urls)} first-level urls found.')
random.shuffle(first_level_urls)

ic = 0
sec_level_url = []
for url in first_level_urls:
    soup = fetcher.get_soup(url)
    slu = collector.get_slurl(url, soup)
    if slu:
        sec_level_url.extend(slu)
    else:
        print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {url} - {len(slu)} urls.')
    ic += 1
    print(f'\r{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Fetching second-level urls - {ic}/{len(first_level_urls)}', end='')

sec_level_url = [item for item in sec_level_url if item not in first_level_urls] # current slu
# exclude duplicated sec-level urls
with open(r'data\second_level_urls.txt', 'r', encoding='utf-8') as f:
    old_slu = [item.strip() for item in f]
sec_level_url = [item for item in sec_level_url if item not in old_slu]
# export
with open(r'data\second_level_urls_July.txt', 'a', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in sec_level_url)
print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} second-level urls saved successfully.')