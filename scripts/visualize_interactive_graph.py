from collections import Counter
import sys
import numpy as np
import pymysql

from .utils import *
from src.utils import get_colormap
from pyvis.network import Network


def export_graph_to_html(output_file='graph.html', category_info=True, appendix_info=True, select_menu=True, filter_menu=True):
    graph = builder.build_graph("d2w", category_info=category_info, appendix_info=appendix_info, 
        preprocessing_callback=Preprocessor(return_type="str"),
    )
    g = Network(directed=True, select_menu=select_menu, filter_menu=filter_menu)
    n_color_palette = get_colormap(graph.ntypes, palette="tab10_r")
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
                title = "[{language}]\n{word}\n\n{wikiUrl}".format_map(node)
                g.add_node(n_id=node['id'], label=node['word'], color=n_color_palette[ntype], title=title)

    # graph = dgl.to_homogeneous(builder.graph)
    # print(graph.ndata)
    # print(graph)
    e_color_palette = get_colormap(set(graph.etypes), palette="Accent_r")
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
        g.add_edge(source=s, to=d, label=r, value=np.log(c + 1), color=e_color_palette[r])

    g.barnes_hut()
    g.save_graph(output_file)