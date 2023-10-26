import os
import json
import re
import sys

sys.path.append('.')
import pymysql


from wiktionaryparser.collector import Collector
from wiktionaryparser.core import WiktionaryParser
from wiktionaryparser.preprocessing import Preprocessor

parser = WiktionaryParser()
prep = Preprocessor()

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)

datasets = []
root, dirs, _ = next(os.walk('D:\Datasets'))

for d in dirs:
    d_ = os.path.join(root, d)
    for f in os.listdir(d_):
        path = os.path.join(d_, f)
        f = re.sub('\.\w+$', '', f)
        dataset = collector.adapt_csv_dataset(path, dataset_name=f, task=d)
        collector.insert_data(dataset, dataset_name=f, task=d)
