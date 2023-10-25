import sys
sys.path.append('.')
import pymysql
from wiktionaryparser.collector import Collector
import json
import tqdm

# nltk.download('punkt')

from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.graph import Builder

parser = WiktionaryParser()
# parser.set_default_language("arabic")

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)
builder = Builder(conn)

fetched_data = {}
saved_data = []
orphan_nodes = builder.get_orphan_nodes()
pbar = tqdm.tqdm(orphan_nodes)
for node in pbar:
    pbar.set_postfix_str(f"{collector.base_url}{node.get('wikiUrl')}")
    fetched_data.update(parser.fetch_all_potential(node.get('word'), node.get('language')))

for k in fetched_data:
    element = fetched_data[k]
    saved_data += collector.save_word(element, save_to_db=True)

with open('missingOut.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(saved_data, indent=4, ensure_ascii=False))
