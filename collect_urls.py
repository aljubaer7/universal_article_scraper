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
        Keep only urls of main category.
        Keep urls with short path < 32 (usual category text length)
        Eg. tech, environment, health, business, science-technology-environment
        '''

        flu = set()
        for url in urls:
            parts = url.split('/')
            if len(parts) > 3:
                category_url = f'{parts[0]}//{parts[2]}/{parts[3]}'
                flu.add(category_url)
        
        # exclude if category is > 32
        return [
            item for item in list(flu)
            if len(item.split('/')[-1]) < 32
            and '?' not in item
            and '@' not in item
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
        # get base-url
        parsed = urlparse(url)
        base_url = f'{parsed.scheme}://{parsed.netloc}'

        all_urls = self.get_urls(base_url, soup) # get all available urls
        slu = []
        for url in all_urls:
            tail = url.rstrip('/').split('/')[-1]
            if 'article' in tail or tail.count('-') > 3:
                slu.append(url)
        return slu


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
        