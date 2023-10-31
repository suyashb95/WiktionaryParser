import json
import sys
import pymysql
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import GraphBuilder

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)
graph_data = builder.word2word()
g = builder.build_graph(instance="d2w",
    preprocessing_callback=Preprocessor(return_type="str"),
    nodes_palette="tab10_r", edges_palette="Set1", filter_menu=True, height='100vh', width='50vw', 
)

g.save_graph('example.html')

