import json
import sys
import langcodes
import numpy as np
import pymysql
import matplotlib.pyplot as plt
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import Builder
from wiktionaryparser.utils import get_colormap

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
g = builder.get_pyvis_graph(
    preprocessing_callback=Preprocessor(return_type="str"),
    nodes_palette="Set1", edges_palette="Set1", filter_menu=True
)

g_options = {
    "physics": {"enabled": False},
    "node": {"size": 100}
}
# g.barnes_hut(spring_length=5)
g.options.set(
    f"""
    var options = {json.dumps(g_options, indent=2)}
"""
)
g.save_graph("example.html")

# # Embed the custom JavaScript in the HTML file
# with open("example.html", "a") as html_file:
#     html_file.write(f"<script>{custom_js}</script>")

