import sys
import re
from unittest import result
import tqdm
sys.path.append('.')
import json

import pymysql
from wiktionaryparser.collector import Collector
import nltk

from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.core import WiktionaryParser


def main(text_words):
    results = []

    prep = Preprocessor(stemmer=nltk.stem.ARLSTem())
    parser = WiktionaryParser()
    parser.set_default_language("arabic")

    conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
    coll = Collector(conn)
    coll.erase_db()


    for word, lang in tqdm.tqdm(text_words):
        no_spaces_word = re.sub('\s', '_', word)
        if word != no_spaces_word: #If word has space, e.q to saying word is an entity
            fetched_data = {word: parser.fetch(no_spaces_word, language=lang)}
        else:
            prepped_word = ' '.join(prep(word)) #[0]
            fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
        for k in fetched_data:
            element = fetched_data[k]
            results += coll.save_word(element, save_to_db=True)

    return results

text_words = [
    # ('خيط', 'moroccan arabic'),
    # ('example', 'english'),
    ('سماء', 'arabic'),
    ('الدار البيضاء', 'arabic'),
    ('البيت الأبيض', 'arabic'),
]

results = main(text_words)

with open('wordOut.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
