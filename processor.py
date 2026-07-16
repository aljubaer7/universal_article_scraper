import re
import uuid
import json
import statistics
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter

# pronouns & prepositions
with open(r'data\pnoun_prep.txt', 'r') as f:
    pnoun_preps = [item.strip().lower() for item in f]

import sqlite3
conn = sqlite3.connect(r'data\metadata.db')


dflt_parameters = { # default parameters
    'min_text_lines': 4,
    'avg_line_len': 80,
    'min_text_length': 1000,
    'max_line_len_p': 50,
    'max_tdot': 5,
    'max_colon': 15,
    'max_int_txt_simi': 0.95,
    'max_exr_txt_simi': 0.998,
    'min_sent_score': 0.5
}


# class > TextValidator
class TextValidator:
    def __init__(self, text_lines: list, parameters=dflt_parameters):
        self.text_lines = text_lines
        self.parameters = parameters


    def create_metadata(self):
        if self.text_lines:
            lines: int = len(self.text_lines) # lines inside text-lines
            line_lens: list = [len(i) for i in self.text_lines] # length of each individual line
            text_len: int = sum(line_lens) # total length of text across all lines
            avg: float = round(statistics.mean(line_lens), 2) # average text per line
            max_len_p: float = round(((max(line_lens) / text_len) * 100), 2) # text percentage of largest line
            text = ' '.join(self.text_lines)
            tdot = text.count('...') + text.count('…')
            colon = text.count(':')

            metadata = {'lines': lines, 'text_len': text_len, 'avg_len': avg, 'max_len_p': max_len_p,
                        'tdot': tdot, 'colon': colon}
            return metadata
            
    def is_valid(self) -> bool:
        metadata = self.create_metadata()
        if metadata:
            return (
                        metadata['lines'] > self.parameters['min_text_lines'] and
                        metadata['text_len'] > self.parameters['min_text_length'] and
                        metadata['avg_len'] > self.parameters['avg_line_len'] and
                        metadata['max_len_p'] < self.parameters['max_line_len_p'] and
                        metadata['tdot'] < self.parameters['max_tdot'] and
                        metadata['colon'] < self.parameters['max_colon']
                    )
        else:
            return False
            
    def word_dict(self, text):
        words = re.sub(r"[,.?;:'!()-]", '', text).split()
        return Counter(words)
    def calculate_similarity(self, x, y):
        dict_x = self.word_dict(x)
        dict_y = self.word_dict(y)
        comm_words = set(dict_x.keys()) | set(dict_y.keys())
        matrix_x = np.array([dict_x.get(word, 0) for word in comm_words])
        matrix_y = np.array([dict_y.get(word, 0) for word in comm_words])
        dot_product = np.dot(matrix_x, matrix_y)
        norm_x = np.linalg.norm(matrix_x)
        norm_y = np.linalg.norm(matrix_y)
        norm_xy = norm_x * norm_y
        if norm_xy > 0:
            return dot_product / norm_xy
        else:
            return 0        
    def exclude_simi_lines(self):
        '''Exclude similar lines (internal) from a given list of text-lines'''
        exc_idx = set()
        for l in range(0, len(self.text_lines) - 1):
            for r in range(l + 1, len(self.text_lines)):
                if l != r:
                    similarity = self.calculate_similarity(self.text_lines[l], self.text_lines[r])
                    if len(self.text_lines[l]) > 50 and similarity > self.parameters['max_int_txt_simi']:
                        exc_idx.add(max(l, r))
                    elif len(self.text_lines[l]) < 50 and similarity > self.parameters['max_int_txt_simi'] - 0.05:
                        exc_idx.add(l)
                        exc_idx.add(r)
        uniq_text_lines = [self.text_lines[i] for i in range(len(self.text_lines)) if i not in exc_idx]
        return [
                line for line in uniq_text_lines
                if line.strip()  # Skip empty lines
                and (words := line.split())  # Walrus operator
                and not '|' in line
                and not (words[0][0] == '(' and words[-1][-1] == ')')
                and not (words[0][0] == '[' and words[-1][-1] == ']')
                and not (words[0][0] == '/' and words[-1][-1] == '/')
                and not line.lower().startswith('also read')
                and not line.lower().startswith('read more')
                and not line.lower().startswith('tap here')
                and not (line.lower().startswith('image') and words[-1][-1] not in '.?!')
                and not (line.startswith('Writer') and ':' in line)
            ]

    # nlp scoring
    def sentence_score(self):
        scores = []

        for line in self.text_lines:
            score = 0.999

            # start capitalization
            fst_word = re.sub(r'[^a-zA-Z\s]', '', line.split()[0])
            if not fst_word.istitle():
                score -= 0.40

            # end puncuation
            end_chr = re.sub(r'[^a-zA-Z.!?]', '', line)[-1]
            if end_chr not in ('.', '!', '?'):
                score -= 0.40

            # word count
            word_count = len(line.split())
            if word_count < 5:
                score -= 0.099 * 2

            # UPPER-CASE count
            upper_count = sum([word.isupper() for word in line.split()])
            if upper_count > 5:
                score -= 0.099

            # pronoun preposition count
            pnoun_prep_count = sum([1 if w.lower() in pnoun_preps else 0 for w in line.split()])
            if pnoun_prep_count < 3:
                score -= 0.001 * 2

            scores.append(score)
        return statistics.mean(scores)
    

# class > SearchByArticle
class SearchByArticle:
    def __init__(self, soup, tag='article'):
        self.soup = soup
        self.tag = tag

    def get_article_text(self):
        tags = list({tag.name for tag in self.soup.find_all()})
        if self.tag in tags:
            html_content = self.soup.find(self.tag)
            text_content = [item.text.strip() for item in html_content if item.text.strip()]
            text_lines = [' '.join(line.split()) for line in text_content if line and len(line) > 1]
            
            validator = TextValidator(text_lines)
            if validator.is_valid():
                text_lines = validator.exclude_simi_lines()

                sentence_score = validator.sentence_score()
                # if original_score > 0.45:
                metadata = {'tag': self.tag, 'attribute': 'n/a'}
                metadata.update(validator.create_metadata())
                metadata.update({'sentence_score': sentence_score})
                df = pd.DataFrame([metadata])

                return text_lines, df
        return None, None
    

# class > SearchAttributes
class SearchByAttributes:
    def __init__(self, soup, tags: list, parameters=dflt_parameters):
        self.soup = soup
        self.tags = tags
        self.parameters = parameters

    def get_attributes(self):
        '''Get all attributes within the soup and given tag list.'''
        if self.soup:
            all_attributes = []
            for tag in self.tags:
                attributes = [tags.attrs for tags in self.soup.find_all(tag) if tags.attrs]
                all_attributes.extend(attributes)
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
            final_attributes = [item for item in unique_attributes if list(item.values())[0] not in ('row', 'column')]
            return final_attributes
        else:
            return None
            
    def get_textLines(self, tag, attribute):
        '''Get text lines as list from given single tag and single attribute'''
        html_content = self.soup.find_all(tag, attribute)
        text_content = [r.text.strip() for res in html_content for r in res if r.text.strip()]
        text_lines = [' '.join(line.split()) for line in text_content if line and len(line) > 1]
        validator = TextValidator(text_lines, self.parameters)
        filtered_text_lines = validator.exclude_simi_lines()
        return filtered_text_lines

    # prevent same text processing multiple times by calculating similarity
    def vector_similarity(self, text_lines, text_vector):
        all_text = self.soup.get_text(strip=True).lower()
        all_words = list(dict.fromkeys(re.sub(r"[,.?;:'!()-]", '', all_text).split()))

        text = ' '.join(text_lines).lower()
        words = re.sub(r"[,.?;:'!()-]", '', text).split()
        words_dict = Counter(words)
        x = [words_dict.get(word, 0) for word in all_words] # current text matrix.

        similarities = []
        for i in range(len(text_vector)):
            y = text_vector[i]
            dot_product = np.dot(x, y)
            norm_x = np.linalg.norm(x)
            norm_y = np.linalg.norm(y)
            norm_xy = norm_x * norm_y
            if norm_xy > 0:
                similarity = dot_product / norm_xy
                similarities.append(similarity)
        text_vector.append(x)
        max_simi = max(similarities) if similarities else 0
        return max_simi
        
    def loop_attributes(self):
        text_vector = []
        df = pd.DataFrame()
        attributes: list = self.get_attributes()
        for item in attributes:
            for tag in self.tags:
                text_lines: list = self.get_textLines(tag, item)
                validator = TextValidator(text_lines, self.parameters)
                # clear unwanted lines
                # text_lines: list = validator.clear_lines()
                if validator.is_valid():
                    text_similarity: float = self.vector_similarity(text_lines, text_vector)
                    if text_similarity < self.parameters['max_exr_txt_simi']:
                        # sentence scoring
                        sentence_score = validator.sentence_score()
                        if sentence_score > self.parameters['min_sent_score']:
                        
                            metadata = {'tag': tag, 'attribute': item}
                            metadata.update(validator.create_metadata())
                            metadata.update({'sentence_score': sentence_score})

                            dfr = pd.DataFrame([metadata])
                            df = pd.concat([df, dfr], ignore_index=True)
        if len(df) > 0:
            df = df.sort_values(by='sentence_score', ascending=False, ignore_index=True)
            tag = df.tag.iloc[0]
            attribute = df.attribute.iloc[0]
            text_lines = self.get_textLines(tag, attribute)
            return text_lines, df
        return None, None


# def > save_text(url, title, text_lines, df, text_file, sql=False)
def save_text(url, title, text_lines, df, txt_file, sql=False):
    uid = f'{datetime.now():D%d%m%yT%H%M%S}_{uuid.uuid4().hex}'
    category = ', '.join([item for item in url.rstrip('/').split('/')[3:-1] if not item.isdecimal()])

    
    with open(txt_file, 'a', encoding='utf-8') as f:
        f.write(f'id: {uid}\n')
        f.write(f'url: {url}\n')
        f.write(f'category: {category}\n')
        f.write(f'title: {title}\n')
        f.writelines(f'{line}\n' for line in text_lines)
        # f.write(f'body: {text}\n')
        f.write('\n')
    if sql:
        table_name = f'{txt_file.split("\\")[1].split('.')[0]}_metadata'
        sql = df.copy()
        sql['attribute'] = sql['attribute'].apply(json.dumps)
        # create url column
        sql.insert(0, 'url', url)
        # create id column
        sql.insert(0, 'id', [f'{uid}_{i}' for i in range(len(sql))])
        # send to sql
        sql.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()

