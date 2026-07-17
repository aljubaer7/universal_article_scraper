import random
import fetch_url
from datetime import datetime
import collect_urls
collector = collect_urls.CollectUrls()

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

sec_level_url = [item for item in sec_level_url if item not in first_level_urls] # current slu
# exclude duplicated sec-level urls
with open(r'data\second_level_urls.txt', 'r', encoding='utf-8') as f:
    old_slu = [item.strip() for item in f]
sec_level_url = [item for item in sec_level_url if item not in old_slu]
# export
with open(r'data\second_level_urls.txt', 'a', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in sec_level_url)
print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} second-level urls saved successfully.')