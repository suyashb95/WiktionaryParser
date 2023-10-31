import os
import json
import nltk
from nltk import stem
import sys
sys.path.append('.')

import random
random.seed(222)
from collections import Counter

import pymysql


from wiktionaryparser.graph import GraphBuilder
from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.preprocessing import Normalizer, Preprocessor

parser = WiktionaryParser()
prep = Preprocessor(stemmer=stem.ARLSTem2(), normalizer=Normalizer('أ', alef_norm='ا'))

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)

results = builder.get_dataset()

k = "dataset_name"  # The key for stratification

k_counts = set(entry[k] for entry in results)
sample_size = 5

stratified_samples = []
for unique_k in k_counts:
    entries_with_k = [entry for entry in results if entry.get(k) == unique_k]
    if len(entries_with_k) >= sample_size:
        entries_with_k = random.sample(entries_with_k, sample_size)
        # entries_with_k = entries_with_k[:2]


    for entry in entries_with_k:
        prepped_text = prep(entry.get('text'))
        # tokens = nltk.word_tokenize(prepped_text)
        entry['tokens'] = Counter(prepped_text)
        stratified_samples.append(entry)


with open('dsInfo.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(stratified_samples, indent=4, ensure_ascii=False))
