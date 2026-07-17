import fetch_url
import collect_urls
from datetime import datetime

## get base-urls
with open(r'data\base_urls.txt', 'r') as f:
    base_urls = [item.strip() for item in f]
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(base_urls)} base-urls found.')

# collect first-level urls
ic = 0
first_level_urls = []

for url in base_urls:
    fetcher = fetch_url.UrlFetcher(url)
    soup = fetcher.getby_bs()
    if soup:
        collector = collect_urls.CollectUrls()
        fl_urls = collector.get_flurl(url, soup)
        first_level_urls.extend(fl_urls)
    else:
        fl_urls = []
    ic += 1
    print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Base-url: {url} - {len(fl_urls)} first-level urls found.')


with open(r'data\first_level_urls.txt', 'w', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in first_level_urls)
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO: {len(first_level_urls)} first-level urls saved successfully.')