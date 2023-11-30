from collections import Counter
import dgl
import sys
from matplotlib import pyplot as plt
import pymysql

sys.path.append('.')
from wiktionaryparser.utils import get_colormap
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import GraphBuilder
from pyvis.network import Network
import networkx as nx

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)
graph = builder.build_graph("d2w", category_info=True, appendix_info=True, 
    preprocessing_callback=Preprocessor(return_type="str"),
)



g = Network(directed=True)
color_palette = get_colormap(graph.ntypes, palette="tab10_r")
for n_i, ntype in enumerate(graph.ntypes):
    node_ids = builder.node_ids[ntype]
    ntype_voc = graph.nodes(ntype)
    if len(ntype_voc) < 1:
        continue
    # print('{} ({}):'.format(ntype,len(ntype_voc)))
    for i in ntype_voc:
        i = i.item()
        node_id = node_ids[i]
        node = builder.vocab.get(node_id)
        if node is not None:
            node['i'] = i
            # print('\t {}'.format(node['word']))
            g.add_node(n_id=node['id'], label=node['word'], color=color_palette[ntype])

# graph = dgl.to_homogeneous(builder.graph)
# print(graph.ndata)
# print(graph)
edgelist = []
for etype in graph.canonical_etypes:
    stype, rel, dtype  = etype
    src_node_idx = builder.node_ids[stype]
    dst_node_idx = builder.node_ids[dtype]
    edges = graph.edges(etype=etype)
    edges = tuple(map(lambda x: x.tolist(), edges))
    for s, d in zip(*edges):
        s = src_node_idx[s]
        d = dst_node_idx[d]
        if None not in (s, d):
            edgelist.append((s, rel, d))

edgelist = Counter(edgelist)
for (s, r, d), c in edgelist.items():
    g.add_edge(source=s, to=d, label=r, value=c)
    # print(etype_rel)


g.save_graph('graph.html')