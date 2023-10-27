import json
import sys
import langcodes
import numpy as np
import pymysql
import matplotlib.pyplot as plt
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import Builder
from pyvis.network import Network


conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
preprocess = Preprocessor(return_type="str")
graph_data = builder.word2word()
vocab = builder.get_vocab()

language_map = {w.get('language') for w in vocab}
language_norm = [langcodes.find(l).language if len(str(l)) > 3 and l is not None else l for l in language_map]
language_map = dict(zip(language_map, language_norm))

node_colormap = plt.get_cmap("tab10")(np.linspace(0, 1, 1+len(set(language_norm))))
node_colormap = (node_colormap * 255).astype(int)
node_colormap = [f"rgb({r}, {g}, {b})" for r, g, b, _ in node_colormap]

node_colors = dict(zip(language_map.values(), node_colormap))
print(node_colors)

edge_colors = {r.get('relationshipType') for r in graph_data}
edge_colormap = plt.get_cmap("tab10_r")(np.linspace(0, 1, len(edge_colors)))
edge_colormap = (edge_colormap * 255).astype(int)
edge_colormap = [f"rgb({r}, {g}, {b})" for r, g, b, _ in edge_colormap]

edge_colors = dict(zip(edge_colors, edge_colormap))

g = Network(height='100vh', width='100vw')



for w in vocab:
    lang = w.get('language')
    lang = language_map[lang]
    color = node_colors.get(lang, "black")
    word = preprocess(w.get('word'))
    g.add_node(w.get('id'), label=word, title=word, color=color, hover=True)

for r in graph_data:
    headId = r.get('headId')
    tailId = r.get('tailId')
    head = preprocess(r.get('head'))
    tail = preprocess(r.get('tail'))
    reltype = r.get('relationshipType')

    if headId not in g.nodes:
        g.add_node(headId, label=head)

    if tailId not in g.nodes:
        g.add_node(tailId, label=tail)

    color = edge_colors[reltype]
    g.add_edge(headId, tailId, color=color, label=reltype, hoverWidth=2)



# Add custom JavaScript to toggle edge label visibility on node click
custom_js = """
network.on('click', function (params) {
    if (params.nodes.length > 0) {
        var nodeId = params.nodes[0];
        network.getConnectedEdges(nodeId).forEach(function (edgeId) {
            var edge = network.body.edges[edgeId];
            if (edge.labelModule) {
                edge.labelModule.text.element.style.display = 'block';
            }
        });
    }
});
"""
# g.barnes_hut(spring_length=5)
g.save_graph("example.html")

# # Embed the custom JavaScript in the HTML file
# with open("example.html", "a") as html_file:
#     html_file.write(f"<script>{custom_js}</script>")

