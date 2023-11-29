import dgl
import sys
import pymysql
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import GraphBuilder
from pyvis.network import Network

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)
graph = builder.build_graph("d2w", category_info=True, appendix_info=True, 
    preprocessing_callback=Preprocessor(return_type="str"),
)

# g = builder.build_graph(instance="d2w",
#     # nodes_palette="tab10_r", edges_palette="Set1", filter_menu=True, height='100vh', width='50vw', 
# )


# g = Network(directed=True)
for ntype in graph.ntypes:
    node_ids = builder.node_ids[ntype]
    ntype_voc = builder.graph.nodes(ntype)
    if len(ntype_voc) < 1:
        continue
    print('{} ({}):'.format(ntype,len(ntype_voc)))
    for i in ntype_voc:
        i = i.item()
        node_id = node_ids[i]
        node = builder.vocab.get(node_id)
        if node is not None:
            node['i'] = i
            print('\t', node['word'])

# print(builder.vocab)
# print(builder.node_ids)
