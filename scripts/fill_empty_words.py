import re
import sys

sys.path.append('.')
import pymysql
from wiktionaryparser.collector import Collector
import json
import tqdm

# nltk.download('punkt')

from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.graph import Builder
from wiktionaryparser.preprocessing import Preprocessor

parser = WiktionaryParser()
prep = Preprocessor()
# parser.set_default_language("arabic")

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)
builder = Builder(conn)

if False:
    # BEGINNING OF TEMPORARY SECTION
    text_words = [
        # ('خيط', 'moroccan arabic'),
        # ('example', 'english'),
        # ('سماء', 'arabic'),
        ('الدار البيضاء', 'arabic'),
    ]
    collector.erase_db()
    for word, lang in tqdm.tqdm(text_words):
        no_spaces_word = re.sub('\s', '_', word)
        if word != no_spaces_word: #If word has space, e.q to saying word is an entity
            fetched_data = {word: parser.fetch(no_spaces_word, language=lang)}
        else:
            prepped_word = ' '.join(prep(word)) #[0]
            fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
        for k in fetched_data:
            element = fetched_data[k]
            collector.save_word(element, save_to_db=True)
    # END OF TEMPORARY SECTION


fetched_data = []
saved_data = []
orphan_nodes = builder.get_orphan_nodes()
pbar = tqdm.tqdm(orphan_nodes)
for node in pbar:
    pbar.set_postfix_str(f"{collector.base_url}{node.get('wikiUrl')}")
    fetched_data.extend(parser.fetch(node.get('word'), node.get('language')))


saved_data = collector.save_word(fetched_data, save_to_db=True)

with open('missingOut.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(saved_data, indent=4, ensure_ascii=False))
