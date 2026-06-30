import fetch_url
import attribute_processor
import sentence_processor

import random
from datetime import datetime

text_file = r'data\text_dataset_b.txt'
with open(r'data\level_2_urls.txt', 'r') as f:
    urls = [item.strip() for item in f]
random.shuffle(urls)

tags = ['div', 'span', 'article', 'section']
# check visited urls
with open(r'data\visited_urls.txt', 'r', encoding='utf-8') as f:
    visited_urls = [item.strip() for item in f]
urls = [url for url in urls if url not in visited_urls]
print(f'{len(urls)} unique urls found!\n')

# Loop urls
ic = 0
error = 0
visited = 0

for url in urls[0:30]:
    ident = f'{datetime.now():D%d%m%yT%H%M%S}'
    # soup = fetch_url.fetch_url(url)
    soup = fetch_url.get_saved_soup(url)
    if soup == None:
        error += 1
    else:
        error = 0
        if soup.title and len(soup) > 1:
            # main process----------------------------------------------------/
            title = soup.title.text.strip().split('|')[0].strip()
            attributes = attribute_processor.get_attributes(soup, tags) # get all available attributes in html
            tag, attribute = attribute_processor.get_tag_attribute(ident, url, soup, tags, attributes) # get one appropriate tag and attribute
            if tag:
                text_lines = attribute_processor.attributes_to_text_lines(soup, tag, attribute)
                # sentences = sentence_processor.get_sentences(text_lines)
                # save text as text file
                text = ' '.join(text_lines)
                sentence_processor.save_text(ident, url, title, text, text_file)
                # end process----------------------------------------------------/
                # with open(r'data\visited_urls.txt', 'a', encoding='utf-8') as f:
                #     f.write(f'{url}\n')

    if error == 4:
        print('\n4 consecutive errors!!')
        break
    ic += 1
    print(f'\r{ic}/{len(urls)}', end='')

