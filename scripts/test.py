from distutils.command import build
import json
import sys
import langcodes
import numpy as np
import pymysql
import matplotlib.pyplot as plt
sys.path.append('.')
from wiktionaryparser.preprocessing import Preprocessor
from wiktionaryparser.graph import GraphBuilder
from wiktionaryparser.utils import get_colormap

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
builder = GraphBuilder(conn)
words = builder.get_vocab(False)
print(words[0].keys())