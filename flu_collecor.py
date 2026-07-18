from datetime import datetime
import fetch_url
fetcher = fetch_url.UrlFetcher(fallback=True)
import collect_urls
collector = collect_urls.CollectUrls()

## get base-urls
with open(r'data\base_urls.txt', 'r') as f:
    base_urls = [item.strip() for item in f]
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  {len(base_urls)} base-urls found.')

# collect first-level urls
ic = 0
first_level_urls = []

for url in base_urls:
    soup = fetcher.get_soup(url)
    fl_urls = collector.get_flurl(url, soup)
    if fl_urls:
        first_level_urls.extend(fl_urls)
    ic += 1
    print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO:  Base-url: {url} - {len(fl_urls)} first-level urls found.')


with open(r'data\first_level_urls.txt', 'w', encoding='utf-8') as f:
    f.writelines(f'{item}\n' for item in first_level_urls)
print(f'{datetime.now():%d.%m.%yT%H:%M:%S} INFO: {len(first_level_urls)} first-level urls saved successfully.')