## get base-urls
with open(r'data\base_urls.txt', 'r') as f:
    base_urls = [item.strip() for item in f]
print(f'{len(base_urls)} base-urls found.')