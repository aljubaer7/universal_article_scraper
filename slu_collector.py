import random
from datetime import datetime

import fetch_url
fetcher = fetch_url.UrlFetcher()
import collect_urls
collector = collect_urls.CollectUrls()

# input-output text-file name
in_text_file = r'data\first_level_urls.txt'
out_txt_file = r'data\second_level_urls.txt'
# clear output file
with open(out_txt_file, 'w', encoding='utf-8') as f:
    f.write('')

first_level_urls = open(in_text_file, 'r', encoding='utf-8').read().split()
random.shuffle(first_level_urls)
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(first_level_urls)} first-level urls found.')

ic = 0
for url in first_level_urls[0:10]:
    soup = fetcher.get_soup(url)
    slu = collector.get_slurl(url, soup)
    if slu:
        with open(out_txt_file, 'a', encoding='utf-8') as f:
            f.writelines(f'{item}\n' for item in slu)

    ic += 1
    print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {ic}/{len(first_level_urls)} | {url} - {len(slu)} urls.')

# # current slu
sec_level_url = open(out_txt_file, 'r', encoding='utf-8').read().split()
print(f'\n{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(sec_level_url)} second-level urls saved successfully.')