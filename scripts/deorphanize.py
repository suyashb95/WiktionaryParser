import sys
import re
import tqdm


sys.path.append('.')

import pymysql
from wiktionaryparser.collector import Collector

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

print(orphan_lex[0].keys())
text_words = sorted({(w['word'], w['id'], w.get('language')) for w in orphan_lex})
# print(text_words)
text_words = tqdm.tqdm(text_words)
for word, id, lang in text_words:
    no_spaces_word = re.sub('\s', '_', word)
    if word != no_spaces_word: #If word has space, e.q to saying word is an entity
        fetched_data = {word: parser.fetch(no_spaces_word, language=lang)}
    else:
        prepped_word = ' '.join(prep(word)) #[0]
        fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
    for k in fetched_data:
        element = fetched_data[k]

        #Add original id so that it matches during the update
        for i in range(len(element)):
            element[i].update({'id': id})
        results += coll.save_word(element, save_to_db=True, save_orphan=False)


# with open('orphOut.json', 'w', encoding="utf8") as f:
#     f.write(json.dumps(results, indent=4, ensure_ascii=False))

print(len(builder.get_orphan_nodes()))
    
