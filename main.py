import fetch_url
import processor as pr


txt_file = r'data\oop_test_b.txt'
tags = ['div', 'span', 'article', 'section']
parameters ={
    'min_text_lines': 6,
    'avg_line_len': 100,
    'min_text_length': 1000,
    'max_line_len_p': 40,
    'max_tdot': 3,
    'max_colon': 12,
    'max_int_txt_simi': 0.95,
    'max_exr_txt_simi': 0.998,
    'min_sent_score': 0.60
}

with open(r'data\flt_sec_level_urls.txt', 'r') as f:
    urls = [item.strip() for item in f]
# check visited urls
with open(r'data\visited_urls.txt', 'r', encoding='utf-8') as f:
    visited_urls = [item.strip() for item in f]
urls = [url for url in urls if url not in visited_urls]
print(f'{len(urls)} unique urls found!\n')




# Loop urls
ic = 0
error = 0
visited = 0

for url in urls:
    soup = fetch_url.get_soup(url)
    # soup = fetch_url.get_saved_soup(url)
    if soup == None:
        error += 1
    else:
        # save soup for later use
        fetch_url.save_soup(soup, url)

        error = 0
        if soup.title:
            # main process----------------------------------------------------/
            title = soup.title.text.strip().split('|')[0].strip()
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

