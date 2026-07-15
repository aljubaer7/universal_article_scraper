# import fetch_url
from urllib.parse import urlparse, urljoin
import random

with open(r'data\excludeables.txt', 'r') as f: # excludeable domains
    excludeables = [item.strip() for item in f]

class CollectUrls:

    def filter_urls(self, base_url: str, raw_urls: list) -> list:
        """
        Filter raw URLs to keep only valid internal links.
        Input: List of raw urls and a base url
        Output: List of filtered urls
        """
        filtered_urls = []
        for url in raw_urls:
            # Not a URL
            if not url.startswith(("http://", "https://")):
                continue
            # Exclude base URL
            if url.rstrip("/") == base_url.rstrip("/"):
                continue
            # Exclude from the given list, eg. social-media pages, terms and condition pages
            if any(link in url for link in excludeables):
                continue
            # Exclude external domains
            if not urlparse(url).netloc == urlparse(base_url).netloc:
                continue
            filtered_urls.append(url)
        return filtered_urls


    def get_urls(self, base_url: str, soup, filtr=True) -> list:
        '''
        Get and filter all links available inside the given url.
        Only returns links of same domains.
        '''
        # fetcher = fetch_url.UrlFetcher(base_url)
        # soup = fetcher.get_soup()
        if soup:
            raw_urls = list(dict.fromkeys([
                urljoin(base_url, a.get('href'))
                for a in soup.find_all('a')
                if a.get('href')
            ]))
            if filtr:
                return self.filter_urls(base_url, raw_urls)
            else:
                return raw_urls
        return []


    def get_main_category(self, urls: list) -> list:
        '''
        Keep only urls of main category by comparing with eatch other.
        Keep urls with short path < 32 (usual category text length)
        Eg. tech, environment, health, business, science-technology-environment
        '''
        exc_idx = set() # index of excludeable urls
        for l in range(0, len(urls) - 1):
            for r in range(l + 1, len(urls)):
                if l != r:
                    # one url is from other url's category
                    if urls[l] in urls[r] or urls[r] in urls[l]:
                        if len(urls[l]) < len(urls[r]):
                            exc_idx.add(r)
                        else:
                            exc_idx.add(l)
        # Exclude by list index
        category_urls = [urls[i] for i in range(len(urls)) if i not in exc_idx]

        # second check if any non-category urls exists
        short_path_urls = set()
        for url in category_urls:
            if url.count('/') > 3: # exclude multiple path
                parts = url.split('/')
                short_path = f'{parts[0]}//{parts[2]}/{parts[3]}'
                short_path_urls.add(short_path)
            else:
                short_path_urls.add(url)

        # exclude if category is > 32
        return [
            item for item in short_path_urls
            if len(item.split('/')[-1]) < 32
            and '?' not in item
        ]
    

    def get_flurl(self, url: str, soup) -> list: # get first level url
        '''
        Returns first-level category urls followed by same domain.
        '''
        all_urls = self.get_urls(url, soup) # get all available urls
        category_urls = self.get_main_category(all_urls)
        if category_urls:
            return category_urls
        return []
    

    def get_slurl(self, url: str, soup) -> list: # get second level url
        '''
        Returns second-level category urls followed by same domain.
        '''
        all_urls = self.get_urls(url, soup) # get all available urls
        # only follow category
        return [
            item for item in all_urls
            if url in item
        ]


    def run_url_collector(self, base_urls: list) ->list:
        '''
        Loop through given base urls list
        Collect first-level urls and second-level urls 
        '''

        first_level_urls = []
        for url in base_urls:
            first_level = self.get_flurl(url)
            if first_level:
                first_level_urls.extend(first_level)
            
        # shuffle first_level_urls
        random.shuffle(first_level_urls)

        sec_level_url = []
        for url in first_level_urls:
            sec_level = self.get_slurl(url)
            if sec_level:
                for item in sec_level:
                    tail = '/'.join(item.split('/')[4:])
                    if 'article' in tail or tail.count('-') > 3:
                        sec_level_url.extend(item)
        
        return [item for item in sec_level_url if item not in first_level_urls]
        