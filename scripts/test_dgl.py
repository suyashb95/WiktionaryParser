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
g = builder.get_homo_graph("d2w", category_info=True, appendix_info=True)

    

# print(g.etypes)
# print(g.ntypes)
# for e in sorted(g.canonical_etypes):
#     print(e)
# model = create_combined_model(100, 64, 3)
# model(g)

print(g)

# print(g.ndata['h'])
# print(builder.node_ids)
