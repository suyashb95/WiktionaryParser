import sys
import re
import tqdm


sys.path.append('.')
import json

import pymysql
from wiktionaryparser.collector import Collector
import nltk

from wiktionaryparser.utils import convert_language
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import GraphBuilder
from wiktionaryparser.core import WiktionaryParser


# text_words = ['example']
results = []

prep = Preprocessor(unshakl=True)
parser = WiktionaryParser()
parser.set_default_language("arabic")

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
coll = Collector(conn)
builder = GraphBuilder(conn)
orphan_lex = builder.get_orphan_nodes()
for w in orphan_lex:
    if w.get('language') is None:
        w['language'] = "english"
    else:
        w['language'] = convert_language(w['language'], format="long")

text_words = sorted({(w['word'], w.get('language')) for w in orphan_lex})
# print(text_words)
text_words = tqdm.tqdm(text_words)
for word, lang in text_words:
    no_spaces_word = re.sub('\s', '_', prep(word)[0])
    for nsw in [no_spaces_word.capitalize(), no_spaces_word.lower()]:
        fetched_data = parser.fetch(word, query=nsw, language=lang)

        for e in fetched_data:
            text_words.set_postfix_str((e['word'], e['query']))
        results += coll.save_word(fetched_data, save_to_db=True, save_orphan=False, save_mentions=False)

with open('orphOut.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
