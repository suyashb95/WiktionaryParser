import json
import sys
import pymysql
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import Builder

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = Builder(conn)
builder.word2word()
g = builder.get_pyvis_graph(instance="d2w",
    preprocessing_callback=Preprocessor(return_type="str"),
    nodes_palette="tab10_r", edges_palette="Set1", filter_menu=True, height='100vh', width='50vw', 
)

g.save_graph('example.html')

# custom_js = """
# // Get references to the elements
# const cardDiv = document.querySelector('.card');
# const configDiv = document.querySelector('#config');
# const networkDiv = document.querySelector('#mynetwork');
# // Create a new div to wrap the 'config' div
# const newDiv = document.createElement('div');
# newDiv.setAttribute('class', 'container')
# if (true) {
#     // Check if both elements exist in the DOM
#     if (networkDiv) {
    
#     // Append the 'config' div to the new div
#     newDiv.appendChild(networkDiv);
#     // Append the new div inside the 'card' div
#     cardDiv.appendChild(newDiv);
#     }
#     if (configDiv) {
    
#     // Append the 'config' div to the new div
#     newDiv.appendChild(configDiv);
#     // Append the new div inside the 'card' div
#     cardDiv.appendChild(newDiv);
#     }
# }
# else {
#   console.log("One or both of the elements were not found.");
# }
# """

# Embed the custom JavaScript in the HTML file
# with open("example.html", "a") as html_file:
#     html_file.write(f"<script>{custom_js}</script>")
#     # html_file.write(f"<style>{custom_css}</style>")

