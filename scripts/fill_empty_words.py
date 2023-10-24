import sys
sys.path.append('.')
import pymysql
from wiktionaryparser.collector import Collector
import tqdm

# nltk.download('punkt')

from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.graph import Builder

parser = WiktionaryParser()
# parser.set_default_language("arabic")

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)
builder = Builder(conn)

fetched_data = []
orphan_nodes = builder.get_orphan_nodes()
for node in orphan_nodes:
    print(node)
    fetched_data += parser.fetch(node.get('word'), node.get('language'))
    break

saved_data = collector.save_word(fetched_data)

