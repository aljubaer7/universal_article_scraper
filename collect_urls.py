# import fetch_url
from urllib.parse import urlparse, urljoin
import random

with open(r'data\excludeables.txt', 'r') as f: # excludeable domains
    excludeables = [item.strip() for item in f]

class CollectUrls:

    def is_valid_url(self, base_url: str, url: str) -> bool:
        """
        Check whether a single URL is a valid internal link.
        Input: A single url and the base url
        Output: True if the url passes all checks, else False
        """
        # Not a URL
        if urlparse(url).scheme not in ("http", "https"):
            return False
        # Exclude base URL
        if url.rstrip("/") == base_url.rstrip("/"):
            return False
        # Exclude from the given list, eg. social-media pages, terms and condition pages
        if any(link in url for link in excludeables):
            return False
        # Exclude external domains
        base_domain = urlparse(base_url).netloc.removeprefix("www.")
        url_domain = urlparse(url).netloc.removeprefix("www.")

        return base_domain == url_domain

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
            base_domain = urlparse(base_url).netloc.split('www.')[-1].split('.')[0]
            url_domain = urlparse(url).netloc.split('www.')[-1].split('.')[0]


            # if not urlparse(url).netloc == urlparse(base_url).netloc:
            if not base_domain == url_domain:
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
    

    def get_slurl(self, flu: str, soup, follow_category=True, max_url=25) -> list: # get second level url
        '''
        Returns second-level category urls followed by same domain.
        '''
        # get valid urls with title
        urls = {}
        for i in soup.find_all('a'):
            title = ' '.join(i.text.strip().replace('\n', ' ').split())
            url = urljoin(flu, i.get('href'))
            if self.is_valid_url(flu, url):
                urls[url] = title

        # filter by title and url-tail
        slu = []
        for url, title in urls.items():
            hyp_cnt = max(urlparse(url).path.split('/'), key=len).count('-')
            if hyp_cnt > 4 or len(title) > 35:
                slu.append(url)
        
        # filter by category
        if follow_category:
            if len(slu) <= max_url:
                return slu
            elif len(slu) > max_url:
                parsed = urlparse(flu)
                category = [p for p in parsed.path.split('/') if p]
                ctg_slu = [u for u in slu if any([f'/{c}/' in u for c in category])] if category else slu
                if len(ctg_slu) >= max_url:
                    return ctg_slu[:max_url]
                elif len(ctg_slu) < max_url:
                    non_cat = [u for u in slu if u not in ctg_slu]
                    short = max_url - len(ctg_slu)
                    return ctg_slu + non_cat[:short]
        return slu
        