import sys
import pymysql
import dgl
import torch
sys.path.append('.')
from wiktionaryparser.feature_extraction import FeatureExtractor
from wiktionaryparser.graph import Builder
from models.model import create_classification_model

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
feature_ext = FeatureExtractor(conn, embedding_type="category_embedding")
g, node_ids_inv = builder.get_hetero_graph("w2w")
for ntype in g.ntypes:
    token_ids = [
        node_ids_inv.get(node_id.item()) for node_id in g.nodes(ntype)
    ]
    token_ids = [feature_ext(i) for i in token_ids]
    g.nodes[ntype].data['features'] = torch.tensor(token_ids)
    


model = create_classification_model(100, 64, 3)
model(g)


