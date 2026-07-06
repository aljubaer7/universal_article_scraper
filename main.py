import fetch_url
import processor as pr


txt_file = r'data\oop_test.txt'
with open(r'data\level_2_urls.txt', 'r') as f:
    urls = [item.strip() for item in f]
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

for url in urls[0:10]:
    # soup = fetch_url.fetch_url(url)
    soup = fetch_url.get_saved_soup(url)
    if soup == None:
        error += 1
    else:
        error = 0
        if soup.title and len(soup) > 1:
            # main process----------------------------------------------------/
            title = soup.title.text.strip().split('|')[0]
            article = pr.SearchByArticle(soup)
            text_lines, df = article.get_article_text()
            if text_lines:
                pr.save_text(url, title, text_lines, df, txt_file, sql=True)
            else:
                text = pr.SearchByAttributes(soup, tags)
                text_lines, df = text.loop_attributes()
                if text_lines:
                    pr.save_text(url, title, text_lines, df, txt_file, sql=True)
                # end process----------------------------------------------------/
                with open(r'data\visited_urls.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}\n')

    if error == 4:
        print('\n4 consecutive errors!!')
        break
    ic += 1
    print(f'\r{ic}/{len(urls)}', end='')

