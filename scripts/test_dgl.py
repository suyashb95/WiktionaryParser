import sys
import pymysql
sys.path.append('.')
from wiktionaryparser.graph import Builder

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
g = builder.get_hetero_graph("w2w")


