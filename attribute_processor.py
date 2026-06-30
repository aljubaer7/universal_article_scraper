import sentence_processor

import pandas as pd
import statistics
import numpy as np
import json
import re
from collections import Counter
import sqlite3
conn = sqlite3.connect(r'data\metadata.db')

import joblib
model = joblib.load(r'data\sentense_score_80.pkl')

table_name = 'meta_3'



def append_to_sql(table_name, df):
    df.to_sql(table_name, conn, if_exists='append', index=False)

def log_error(ident, url):
    with open(r'data\error_log.txt', 'a', encoding='utf-8') as f:
        f.write(f'{ident}\n')
        f.write(f'{url}\n')

def max_similarity(all_words, text_lines, matrix):
    text = ' '.join(text_lines).lower()
    words = re.sub(r"[,.?;:'!()-]", '', text).split()
    words_dict = Counter(words)
    x = [words_dict.get(word, 0) for word in all_words] # current text matrix.

    similarities = []
    for i in range(len(matrix)):
        y = matrix[i]
        dot_product = np.dot(x, y)
        norm_x = np.linalg.norm(x)
        norm_y = np.linalg.norm(y)
        norm_xy = norm_x * norm_y
        if norm_xy > 0:
            similarity = dot_product / norm_xy
            similarities.append(similarity)
    max_simi = max(similarities) if similarities else 0
    matrix.append(x)
    return max_simi

def get_attributes(soup, tags):
    '''
    Get all attributes within the soup and given tag list.
    '''
    all_attributes = []
    for tag in tags:
        attributes = [tags.attrs for tags in soup.find_all(tag) if tags.attrs]
        all_attributes.extend(attributes)
    # attributes = [tags.attrs for tags in soup.find_all(tag) if tags.attrs]
    seen = set()
    unique_attributes = []
    for d in all_attributes:
        if not d:
            continue
        first_key = next(iter(d))
        first_value = d[first_key]
        
        
        if isinstance(first_value, list):
            key_value = ' '.join(first_value)
        else:
            key_value = first_value
        identifier = (first_key, key_value)
        if identifier not in seen:
            seen.add(identifier)
            unique_attributes.append({first_key: key_value})
    final_attributes = [item for item in unique_attributes if list(item.values())[0] not in ('row', 'column')] # 'image', 'video'  
    return  final_attributes

def attributes_to_text_lines(soup, tag, attribute):
    '''
    Get text lines as list from given tag and attribute
    '''
    result = soup.find_all(tag, attribute)
    text_content = [r.text.strip() for res in result for r in res if r.text.strip()]
    # text_lines = [i.replace('\xa0', ' ').replace('\ufeff', '') for line in text_content for i in line.split('\n')
    #             if i.strip() # exclude blank lines
    #             and not any(l in i for l in ['\t', '\r', '...'])] # exclude \t, \r
    # text_lines = [line for line in text_lines if len(line) > 2]
    text_lines = [' '.join(line.split()) for line in text_content if line and len(line) > 1]
    return text_lines

def get_tag_attribute(ident, url, soup, tags, attributes):
    all_text = soup.get_text(strip=True).lower()
    all_words = list(dict.fromkeys(re.sub(r"[,.?;:'!()-]", '', all_text).split()))
    matrix = []
    df = pd.DataFrame()
    for item in attributes:
        for tag in tags:
            text_lines = attributes_to_text_lines(soup, tag, item)
            text_lines = sentence_processor.exclude_simi_lines(text_lines)
            if len(text_lines) > 6:
                lengths = [len(i) for i in text_lines]
                total_len = sum(lengths)
                # left dataframe
                dfl = pd.DataFrame([{'id': ident, 'url': url, 'tag': tag, 'attrib': item, 'total_len': total_len}])
                if total_len > 1000:
                    avg = round(statistics.mean(lengths))
                    if avg > 98:
                        # similarity
                        max_simi = max_similarity(all_words, text_lines, matrix)
                        if max_simi < 0.998:
                            max_len_p = round(((max(lengths) / total_len) * 100), 2) # max length percentage
                            if max_len_p < 40:
                                # end punctuation percentage
                                end_punct_p = round(((sum([0 if not line[-1] in ('.', '!', '?') else 1 for line in text_lines]) / len(text_lines)) * 100), 2)
                                if end_punct_p > 30:
                                    q1, q2, q3 = statistics.quantiles(lengths, n=4)
                                    below_avg_p = round(((sum([0 if i < avg else 1 for i in lengths]) / len(text_lines)) * 100), 2)
                                    # prediction -> right dataframe
                                    dfX = pd.DataFrame([{'avg_len': avg, 'first_q': q1, 'sec_q': q2, 'max_len_p': max_len_p, 'below_avg_p': below_avg_p, 'end_punct_p': end_punct_p}])
                                    dfX['pred_score'] = model.predict(dfX)
                                    # original
                                    sent_score = sentence_processor.sentence_scoring(text_lines)
                                    avg_sent_score = statistics.mean(sent_score)
                                    if avg_sent_score > 0.45:
                                        # dataframe
                                        dfX['sentence_score'] = avg_sent_score
                                        dfr = pd.concat([dfl, dfX], axis=1)
                                        df = pd.concat([df, dfr], ignore_index=True)
    if len(df) > 0:
        df = df.sort_values(by='sentence_score', ascending=False, ignore_index=True)
        tag = df['tag'].iloc[0]
        attribute = df['attrib'].iloc[0]
        # send to sql
        df['attrib'] = df['attrib'].apply(json.dumps)
        append_to_sql(table_name, df)
        return tag, attribute
    else:
        log_error(ident, url)
        return None, None

