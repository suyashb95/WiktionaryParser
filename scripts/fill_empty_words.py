import sys

sys.path.append('.')
import pymysql
import json
import tqdm

from wiktionaryparser.collector import Collector
from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.graph import GraphBuilder
from wiktionaryparser.preprocessing import Preprocessor

parser = WiktionaryParser()
prep = Preprocessor()

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)
builder = GraphBuilder(conn)

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
