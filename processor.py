import re
import uuid
import json
import statistics
import unicodedata
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
    'min_sent_score': 0.50
}


# class > TextValidator
class TextValidator:
    def __init__(self, parameters=dflt_parameters):
        self.parameters = parameters


    def create_metadata(self, text_lines: list):
        if text_lines:
            lines: int = len(text_lines) # lines inside text-lines
            line_lens: list = [len(i) for i in text_lines] # length of each individual line
            text_len: int = sum(line_lens) # total length of text across all lines
            avg: float = round(statistics.mean(line_lens), 2) # average text per line
            max_len_p: float = round(((max(line_lens) / text_len) * 100), 2) # text percentage of largest line
            text = ' '.join(text_lines)
            tdot: str = text.count('...') + text.count('…')
            colon: str = text.count(':')
            # count of unique subjects
            unq_sub: str = len(list(dict.fromkeys([i.split()[0] for i in text_lines])))

            metadata = {'lines': lines, 'text_len': text_len, 'avg_len': avg, 'max_len_p': max_len_p,
                        'tdot': tdot, 'colon': colon, 'unique_sub': unq_sub}
            return metadata
            
    def is_valid(self, text_lines: list) -> bool:
        metadata = self.create_metadata(text_lines)
        if metadata:
            return (
                        metadata['lines'] > self.parameters['min_text_lines'] and
                        metadata['text_len'] > self.parameters['min_text_length'] and
                        metadata['avg_len'] > self.parameters['avg_line_len'] and
                        metadata['max_len_p'] < self.parameters['max_line_len_p'] and
                        metadata['tdot'] < self.parameters['max_tdot'] and
                        metadata['colon'] < self.parameters['max_colon'] and
                        metadata['unique_sub'] > 1
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
    def exclude_simi_lines(self, text_lines: list):
        '''Exclude similar lines (internal) from a given list of text-lines'''
        exc_idx = set()
        for l in range(0, len(text_lines) - 1):
            for r in range(l + 1, len(text_lines)):
                if l != r:
                    similarity = self.calculate_similarity(text_lines[l], text_lines[r])
                    if len(text_lines[l]) > 50 and similarity > self.parameters['max_int_txt_simi']:
                        exc_idx.add(max(l, r))
                    elif len(text_lines[l]) < 50 and similarity > self.parameters['max_int_txt_simi'] - 0.05:
                        exc_idx.add(l)
                        exc_idx.add(r)
        uniq_text_lines = [text_lines[i] for i in range(len(text_lines)) if i not in exc_idx]
        return uniq_text_lines

    def _character_maping(self, text_lines) -> list:
        result = []
        for line in text_lines:
            norm = unicodedata.normalize('NFD', line)
            line = ''.join(char for char in norm if not unicodedata.combining(char))
            line = re.sub(r'[‐‑‒–—―]', '-', line)
            line = re.sub(r'[‘’′]', "'", line)
            line = re.sub(r'[″❝❞“”]', '"', line)
            line = re.sub(r'[^ -~]', '', line)
            # line = ' '.join(line.split())
            result.append(line)
        return result
    def _exclude(self, text_lines):
        return [
                    line for line in text_lines
                    if line.strip()  # Skip empty lines
                    and not '|' in line # exc
                    # Keep updated, follow The Business Standard's Google news channel
                    and not all([i in line.lower() for i in ['follow', 'news', 'channel']])
                    and not all([i in line.lower() for i in ['follow', 'facebook', 'instagram']])
                    and not all([i in line.lower() for i in ['follow', 'subscribe', 'newsletter']])
                    and not all([i in line.lower() for i in ['subscribe', 'news', 'channel']])
                    and not all([i in line.lower() for i in ['comment', 'post', 'view']])
                    and not all([i in line.lower() for i in ['sign up', 'news', 'channel']])
                    and not all([i in line.lower() for i in ['sign up', 'newsletter']])
                    and not all([i in line.lower() for i in ['click', 'download', 'app']])
                    and not all([i in line.lower() for i in ['click', 'more', 'news']])
                    and not all([i in line.lower() for i in ['get', 'latest', 'news']])
                    and not all([i in line.lower() for i in ['latest', 'news', 'update']])
                    and not all([i in line.lower() for i in ['views', 'express', 'author']])
                    and not any([i in line.lower() for i in ['photo:', 'photo :']])
                    and not any([i in line.lower() for i in ['writer:', 'writer :']])
                    and not (line[0] == '(' and line[-1] == ')')
                    and not (line[0] == '[' and line[-1] == ']')
                    and not (line[0] == '/' and line[-1] == '/')
                    and not any([line.lower().startswith(i) for i in ['also read', 'read more', 'tap here', 'related news', 'click here', 'advertise']])
                    and not (line.lower().startswith('image') and line[-1] not in '.?!')
                    and not (line.lower().startswith('getty') and line[-1] not in '.?!')
                    and not (line.lower().startswith('most viewed') and line[-1] not in '.?!')
                    and not (line.lower().startswith('sign in') and line[-1] not in '.?!')
                    and not (line.lower().startswith('read') and line[-1] not in '.?!')
                    and not (line.lower().startswith('watch') and line[-1] not in '.?!')
                    and not (line.lower().startswith('live') and line[-1] not in '.?!')
                ]
    def _replace(self, text_lines) -> list:
        return [line.replace("\'", "′") for line in text_lines]
    def filter_text_lines(self, text_lines) -> list:
        t_lines = list(dict.fromkeys(text_lines))
        t_lines = self._character_maping(t_lines)
        t_lines = self._exclude(t_lines)
        t_lines = self._replace(t_lines)
        return t_lines

    # exclude concatenated words
    def conc_words_count(self, line: str) -> int:
        '''
        Returns concatenated words count as int
        '''
        words = line.split() # list of words
        words = [re.split(r'[^A-Za-z0-9,.?!]', word) for word in words] # split word by special characters
        words = [item for sublist in words for item in sublist] # flattened list
        words = [word for word in words if len(word) > 4] # exclude short words
        count = sum([any([w.isupper() for w in word[1:-1]]) for word in words if not word.isupper()]) # count concateneted words
        return count
    def exc_conc_words(self, text_lines: list, max_conc: int = 6) -> list:
        '''
        Excludes lines if concatenated-words-count is higher than max_conc (given number)
        '''
        return [line for line in text_lines if self.conc_words_count(line) < max_conc]

    # join broken lines
    def _ending_space(self, text):
        return bool(text[-1].isspace())
    def _starting_space(self, text):
        return bool(text[0].isspace())
    def _end_punctuation(self, text):
        text = re.sub(r'[^a-zA-Z0-9:;,.?!]/', '', text)
        return bool(text[-1] in '.?!')
    def _start_capital(self, text):
        if text[0].isnumeric():
            return True
        text = re.sub(r'[^a-zA-Z0-9:;,.?!\s]', '', text)
        return bool(text[0].isupper())
    def join_broken_lines(self, text_lines: list) -> list:
        if len(text_lines) > 3:
            result = []
            previous_line = text_lines[0]
            for i in range(1, len(text_lines)):
                current_line = text_lines[i]
                if not self._ending_space(previous_line) and self._start_capital(current_line):
                    result.append(previous_line)
                    previous_line = current_line
                elif self._end_punctuation(previous_line) and not current_line[0].isalpha(): # previous is good, current not isalpha
                    result.append(previous_line)
                    previous_line = current_line
                else:
                    previous_line = previous_line + current_line
            result.append(current_line)
            return result
        return text_lines

    # nlp scoring
    def sentence_score(self, text_lines: list):
        scores = []

        for line in text_lines:
            score = 0.999

            # start capitalization
            fst_word = re.sub(r'[^a-zA-Z\s]', '', line.split()[0])
            if not fst_word.istitle():
                score -= 0.40

            # end puncuation
            chrs = re.sub(r'[^a-zA-Z.!?]', '', line)
            end_chr = chrs[-1] if chrs else ''
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
    def __init__(self, soup, tag='article', parameters=dflt_parameters):
        self.soup = soup
        self.tag = tag
        self.parameters = parameters

    def get_article_text(self):
        tags = list({tag.name for tag in self.soup.find_all()})
        if self.tag in tags:
            html_content = self.soup.find(self.tag)
            text_content = [item.text.strip() for item in html_content if item.text.strip()]
            text_lines = [' '.join(line.split()) for line in text_content if line and len(line) > 1]

            # filter text_lines
            validator = TextValidator()
            text_lines = validator.filter_text_lines(text_lines)
            text_lines = validator.exc_conc_words(text_lines)
            
            if validator.is_valid(text_lines):

                sentence_score = validator.sentence_score(text_lines)
                if sentence_score > self.parameters['min_sent_score']:
                    metadata = {'tag': self.tag, 'attribute': 'n/a'}
                    metadata.update(validator.create_metadata(text_lines))
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

    def _is_text(self, text):
        return bool(len(re.findall(r'[a-zA-Z,.?!]', text)) > 0)
    
    def get_textLines(self, tag, attribute, filter=True):
        '''Get text lines as list from given single tag and single attribute'''
        html_content = self.soup.find(tag, attribute)
        if html_content:
            all_lines = [c.text.replace('\n', '') for c in html_content]
            text_lines = [line for line in all_lines if self._is_text(line) and '\t' not in line]

            if filter:
                validator = TextValidator(self.parameters)
                text_lines = validator.filter_text_lines(text_lines)
                text_lines = validator.join_broken_lines(text_lines)
                text_lines = validator.exc_conc_words(text_lines)
                text_lines = [' '.join(line.split()) for line in text_lines]
            return text_lines

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
        df = pd.DataFrame()
        attributes: list = self.get_attributes()
        validator = TextValidator(self.parameters)

        for item in attributes:
            for tag in self.tags:
                text_lines: list = self.get_textLines(tag, item)

                if validator.is_valid(text_lines):
                    # sentence scoring
                    sentence_score = validator.sentence_score(text_lines)
                    if sentence_score > self.parameters['min_sent_score']:
                        metadata = {'tag': tag, 'attribute': item}
                        metadata.update(validator.create_metadata(text_lines))
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

