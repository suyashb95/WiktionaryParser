from parameterized import parameterized
import unittest
import json
from wiktionaryparser import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict, List
import nltk
import tqdm
import time
# nltk.download('punkt')

from urllib import parse
import os

parser = WiktionaryParser()

test_words = [
    # ('ἀγγελία', 47719496, ['Ancient Greek']),
    ('البيت_الأبيض', None, ['Arabic']),
    # ('The_White_House', None, ['EnGlish']),
    # ('test', 50342756, ['English']),
    # ('patronise', 49023308, ['English']),
    # ('abiologically', 43781266, ['English']),
    # ('alexin', 50152026, ['English']),
    # ('song', 60388804, ['English']),
    # ('house', 50356446, ['English']),
    # ('correspondent', 61052028, ['English']),
    # ('video', 50291344, ['Latin']),
    # ('seg', 50359832, ['Norwegian Bokmål']),
    # ('aldersblandet', 38616917, ['Norwegian Bokmål']),
    # ('by', 50399022, ['Norwegian Bokmål']),
    # ('for', 50363295, ['Norwegian Bokmål']),
    # ('admiral', 50357597, ['Norwegian Bokmål']),
    # ('heis', 49469949, ['Norwegian Bokmål']),
    # ('konkurs', 48269433, ['Norwegian Bokmål']),
    # ('pantergaupe', 46717478, ['Norwegian Bokmål']),
    # ('maldivisk', 49859434, ['Norwegian Bokmål']),
    # ('house', 50356446, ['Swedish'])
]


text = """
الدوري الإسباني عمل واحدة الدوري الإنجليزي و حسب تسلل من وحي خيال الحكم في هدف فيليكس ، الاوفسايد على توريس اللي مش متداخل اساسا في اللعبة
"""

text_words = nltk.word_tokenize(text)
# text_words = ['من']
results = {}
parser = WiktionaryParser()
parser.include_relation('alternative forms')
for word in tqdm.tqdm(text_words):
    results.update(parser.fetch_all_potential(word=word, language="arabic", old_id=None, verbose=0))
    time.sleep(.5)


with open('testOutput.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
