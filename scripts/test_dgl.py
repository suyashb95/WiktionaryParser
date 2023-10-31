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
embeddings = {
    "category_embedding": FeatureExtractor(conn, embedding_type="category_embedding")
}
g = builder.get_hetero_graph("w2w")
for ntype in g.ntypes:
    token_ids = [
        builder.node_ids.get(node_id.item()) for node_id in g.nodes(ntype)
    ]
    for fn, embed in embeddings.items():
        E = torch.tensor([embed(i) for i in token_ids])
        g.nodes[ntype].data[fn] = E
    


# model = create_combined_model(100, 64, 3)
# model(g)

print(g.ndata['category_embedding'])
