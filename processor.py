import re
import statistics
import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime
import uuid
import json

import sqlite3
conn = sqlite3.connect(r'data\metadata.db')
table_name = 'meta_4_a'

import spacy
nlp = spacy.load('en_core_web_lg')



# class > TextValidator
class TextValidator:
    def __init__(self, text_lines: list):
        self.text_lines = text_lines

    def create_metadata(self):
        if self.text_lines:
            lines: int = len(self.text_lines) # lines inside text-lines
            line_lens: list = [len(i) for i in self.text_lines] # length of each individual line
            text_len: int = sum(line_lens) # total length of text across all lines
            avg: float = statistics.mean(line_lens) # average text per line
            max_len_p: float = round(((max(line_lens) / text_len) * 100), 2) # text percentage of largest line
            end_punct: int = sum([0 if not line[-1] in ('.', '!', '?') else 1 for line in self.text_lines])
            end_punct_p: float = round(((end_punct / lines) * 100), 2) # end punctuation percentage
            text = ' '.join(self.text_lines).split()
            three_dot = sum([1 if '...' in word else 0 for word in text])

            metadata = {'lines': lines, 'text_len': text_len, 'avg_len': avg, 'max_len_p': max_len_p, 'end_punct_p': end_punct_p, 'three_dot': three_dot}
                        # 'below_avg_p': below_avg_p, 'first_q': q1, 'sec_q': q2, 'third_q': q3}
            return metadata
            
    def is_valid(self) -> bool:
        metadata = self.create_metadata()
        if metadata:
            return (
                        metadata['lines'] > 6 and
                        metadata['text_len'] > 1000 and
                        metadata['avg_len'] > 100 and
                        metadata['max_len_p'] < 40 and
                        metadata['end_punct_p'] > 40 and
                        metadata['three_dot'] < 3
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
        '''Exclude similar lines from a given list of text-lines'''
        exc_idx = set()
        for l in range(0, len(self.text_lines) - 1):
            for r in range(l + 1, len(self.text_lines)):
                if l != r:
                    similarity = self.calculate_similarity(self.text_lines[l], self.text_lines[r])
                    if len(self.text_lines[l]) > 50 and similarity > 0.95:
                        exc_idx.add(max(l, r))
                    elif len(self.text_lines[l]) < 50 and similarity > 0.85:
                        exc_idx.add(l)
                        exc_idx.add(r)
        return [self.text_lines[i] for i in range(len(self.text_lines)) if i not in exc_idx]

    # nlp scoring
    def sentence_score(self):
        scores = []
        sentences = [sen.text for line in self.text_lines for sen in nlp(line).sents]
        for sent in sentences:
            score = 0.99
            doc = nlp(sent)
            words = sent.split(' ')
            # start capitalization
            if not sent[0].isupper():
                score += -0.11 * 3
            # end punctuation
            if not sent[-1] in ('.', '!', '?'):
                score += -0.11 * 3
            # upper-case
            if [word.isupper() for word in words].count(True) > 1:
                score += -0.11 * 1.5
            # title-case
            if [token.is_title for token in doc].count(True) / len(words) > 0.60:
                score += -0.11 * 1.5
            # subject
            if not any(token.dep_ in ("nsubj", "nsubjpass") for token in doc):
                score += -0.11 * 2
            # verb
            if not any(token.pos_ == "VERB" for token in doc):
                score += -0.11 * 2
            # out-of-vocab
            if [token.is_oov for token in doc].count(True) > 0:
                score += -0.11 * 1.5
            # space
            if any(token.pos_ == "SPACE" for token in doc):
                score += -0.11
            # length
            if len(words) < 3:
                score += -0.11 * 3
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
    def __init__(self, soup, tags: list):
        self.soup = soup
        self.tags = tags

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
        filtered_text_lines = TextValidator(text_lines).exclude_simi_lines()
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
                validator = TextValidator(text_lines)
                if validator.is_valid():
                    text_similarity: float = self.vector_similarity(text_lines, text_vector)
                    if text_similarity < 0.998:
                        # sentence scoring
                        # pred_score = validator.predict_sentence_score()
                        sentence_score = validator.sentence_score()
                        
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
    uid = f'{datetime.now():D%d%m%yT%H%M%S}_{uuid.uuid4().hex[:15]}'

    
    with open(txt_file, 'a', encoding='utf-8') as f:
        f.write(f'id: {uid}\n')
        f.write(f'url: {url}\n')
        f.write(f'title: {title}\n')
        f.writelines(f'{line}\n' for line in text_lines)
        # f.write(f'body: {text}\n')
        f.write('\n')
    if sql:
        sql = df.copy()
        sql['attribute'] = sql['attribute'].apply(json.dumps)
        # create url column
        sql.insert(0, 'url', url)
        # create id column
        # uid = f'{datetime.now():D%d%m%yT%H%M%S}_{uuid.uuid4().hex[:15]}'
        sql.insert(0, 'id', [f'{uid}_{i}' for i in range(len(sql))])
        # send to sql
        sql.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()