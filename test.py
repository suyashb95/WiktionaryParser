from parameterized import parameterized
import unittest
import json

import pymysql
from wiktionaryparser.collector import Collector
from deepdiff import DeepDiff
from typing import Dict, List
import nltk
import tqdm
import time
# nltk.download('punkt')

from urllib import parse
import os
from wiktionaryparser.graph import Builder

from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.core import WiktionaryParser

test_words = [
    ('البيت_الأبيض', None, ['Arabic']),
]


text = """
الدوري الإسباني عمل واحدة الدوري الإنجليزي و حسب تسلل من وحي خيال الحكم في هدف فيليكس ، الاوفسايد على توريس اللي مش متداخل اساسا في اللعبة
"""

# text_words = nltk.word_tokenize(text)
text_words = [
    # ('خيط', 'moroccan arabic'),
    # ('example', 'english'),
    ('سماء', 'arabic'),
]
# text_words = ['example']
results = {}

prep = Preprocessor(stemmer=nltk.stem.ARLSTem())
parser = WiktionaryParser()
parser.set_default_language("arabic")

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
graph_constructor = Builder(conn)
results = graph_constructor.word2word()
print(results)
# coll = Collector(conn)
# coll.erase_db()


# for word, lang in text_words:
#     prepped_word = prep(word)[0]
#     # fetched_data = {word: parser.fetch(prepped_word, language=lang)}
#     fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
#     for k in fetched_data:
#         element = fetched_data[k]
#         results = coll.save_word(element)

with open('testFetchOutput.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
