import re
import numpy as np
from collections import Counter

import spacy
nlp = spacy.load('en_core_web_lg')

def sentence_scoring(text_lines):
    scores = []
    sentences = [sen.text for line in text_lines for sen in nlp(line).sents]
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

    return scores

def get_sentences(text_lines):
    sentences = [sen.text for line in text_lines for sen in nlp(line).sents]
    return sentences

def save_text(ident, url, title, text, text_file):
    
    with open(text_file, 'a', encoding='utf-8') as f:
        f.write(f'id: {ident}\n')
        f.write(f'url: {url}\n')
        f.write(f'title: {title}\n')
        # f.writelines(f'{line}\n' for line in sentences)
        f.write(f'body: {text}\n')
        f.write('\n')




def word_dict(text):
    words = re.sub(r"[,.?;:'!()-]", '', text).split()
    return Counter(words)
def calculate_similarity(x, y):
    dict_x = word_dict(x)
    dict_y = word_dict(y)
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
def exclude_simi_lines(text_lines: list):
    '''
    Exclude similar lines from a given list of text-lines
    '''
    exc_idx = set()
    for l in range(0, len(text_lines) - 1):
        for r in range(l + 1, len(text_lines)):
            if l != r:
                similarity = calculate_similarity(text_lines[l], text_lines[r])
                if len(text_lines[l]) > 50 and similarity > 0.95:
                    exc_idx.add(max(l, r))
                elif len(text_lines[l]) < 50 and similarity > 0.85:
                    exc_idx.add(l)
                    exc_idx.add(r)
    return [text_lines[i] for i in range(len(text_lines)) if i not in exc_idx]