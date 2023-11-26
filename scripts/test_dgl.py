import sys
import pymysql
import dgl
import torch
sys.path.append('.')
from wiktionaryparser.feature_extraction import FeatureExtractor
from wiktionaryparser.graph import GraphBuilder
from models.model import create_combined_model

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)
g = builder.build_graph("d2w", category_info=True, appendix_info=True)

print(g)