import json
import pymysql
from src.collector import Collector
from src.database import MySQLClient

conn = MySQLClient(host="localhost", user="root", password="", db="knowledge_graph")
coll = Collector(conn)


# def make_graph_from_data(dataset, text_attr="norm"):
#     nodes = {}
#     edges = []
#     data = []
#     with tqdm.notebook.tqdm(total=len(dataset), position=0, desc="Building graph from dataset: ") as pbar:
#         for row in dataset.to_dict('records'):
#             doc = nlp(row['text'])
#             tokenized_sent = []
#             for token in doc:
#                 if not any([erel in token.dep_ for erel in EDGE_RELS]):
#                     continue

#                 e = {a: getattr(token, a) for a in [text_attr, 'dep_', 'head']}
#                 e['head'] = getattr(e['head'], text_attr)
#                 N = {k: getattr(token, k) for k in NODE_ATTRS if k not in ['tensor']}
#                 i = gensim_model.wv.key_to_index.get(getattr(token, text_attr), -1)
#                 N_keys = list(N.keys())
#                 for k in N_keys:
#                     t = type(N[k]).__name__
#                     if t in ["tuple", "generator", "array"]:
#                         N[k] = [str(getattr(n_att, text_attr)) for n_att in N[k]]
#                     elif t == 'ndarray':
#                         N[k] = N[k].tolist()
#                     elif "function" in t or t not in ['str', 'int', 'float', 'bool']:
#                         N.pop(k)

#                 tokenized_sent.append(getattr(token, text_attr))
#                 edges.append(e)
#                 nodes[token.norm] = N

#             data.append({"input_ids": tokenized_sent, "label": row["label"]})
#             pbar.update(1)

#     G = {
#         "nodes": nodes,
#         "edges": edges
#     }
#     data_as_graph = {
#         "partition": "ASTD_2_class",
#         "data": {
#             "graph": G,
#             "task": data
#         }
#     }

#     return data_as_graph #, G, pd.DataFrame(nodes).T, pd.DataFrame(edges)



print(coll.get_datasets())


