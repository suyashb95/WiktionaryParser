import sys
import pymysql
sys.path.append('.')
from wiktionaryparser.graph import Builder

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
graph_data = builder.build_graph("w2w", query_filter={"def.partOfSpeech": ['noun']})

# builder.get_hetero_graph()

