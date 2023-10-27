from pyvis.network import Network
import json
import langcodes
import requests
from bs4 import BeautifulSoup
import csv
import os
import tqdm
import copy
from nltk.stem import *
import pymysql
import itertools
import hashlib

from wiktionaryparser.core import WiktionaryParser 
from wiktionaryparser.utils import flatten_dict, get_colormap


class Builder:
    def __init__(self, conn, 
                 word_table="words", 
                 dataset_table="data", 
                 edge_table="relationships",
                 definitions_table="definitions",
                 force_edge_tail_constraint=False
                ):

        self.conn = conn

        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

        # with open('appendix.json', 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

    @staticmethod
    def get_bidir_rels():
        return ['hyponyms', 'synonyms', 'antonyms']
    

    def word2word(self):
        query = [
            f"SELECT {self.definitions_table}.headword head, {self.definitions_table}.wordId headId, {self.edge_table}.relationshipType, {self.word_table}.word tail, {self.word_table}.id tailId FROM {self.edge_table}",
            f"JOIN {self.definitions_table} ON {self.definitions_table}.id = {self.edge_table}.headDefinitionId",
            f"JOIN {self.word_table} ON {self.word_table}.id = {self.edge_table}.wordId",
        ]
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_vocab(self):
        query = [
            f"SELECT * FROM {self.word_table}",
        ]
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result

    def get_orphan_nodes(self):
        query = [
            f"SELECT word, language, wikiUrl  FROM {self.word_table}",
            "WHERE wikiUrl IS NOT NULL AND query IS NULL",
            "LIMIT 25"
        ]
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_dataset(self, dataset_name=None, task=None):
        query = f"SELECT * from {self.dataset_table}"
        params = {
            "dataset_name": dataset_name,
            "task": task
        }
        params = {k: v for k, v in params.items() if v is not None}
        params = [f"{k}={v}" for k, v in params.items()]
        if len(params) > 0:
            params = " AND ".join(params)
            query = query + " WHERE " + params
        
        cur = self.conn.cursor()
        cur.execute(query)

        result_set = []
        cur_keys = [desc[0] for desc in cur.description]
        for c in cur.fetchall():
            result_set.append(dict(zip(cur_keys, c)))

        return result_set
    
    def get_pyvis_graph(self, instance="w2w", preprocessing_callback=None, nodes_palette="tab10", edges_palette="tab10"):
        g = Network(height='100vh', width='100vw')

        if instance == "w2w":
            graph_data = self.word2word()
        else:
            return g

        vocab = self.get_vocab()
        if preprocessing_callback is None:
            preprocessing_callback = lambda x: x

        language_map = {w.get('language') for w in vocab}
        language_norm = [langcodes.find(l).language if len(str(l)) > 3 and l is not None else l for l in language_map]
        language_map = dict(zip(language_map, language_norm))

        edge_labels = {r.get('relationshipType') for r in graph_data}

        node_colors = get_colormap(language_norm, palette=nodes_palette)
        edge_colors = get_colormap(edge_labels, palette=edges_palette)



        for w in vocab:
            lang = w.get('language')
            lang = language_map[lang]
            color = node_colors.get(lang, "black")
            word = preprocessing_callback(w.get('word'))
            title = f"{word} ({lang})"
            g.add_node(w.get('id'), label=word, title=title, color=color, hover=True)

        for r in graph_data:
            headId = r.get('headId')
            tailId = r.get('tailId')
            head = preprocessing_callback(r.get('head'))
            tail = preprocessing_callback(r.get('tail'))
            reltype = r.get('relationshipType')

            if headId not in g.nodes:
                g.add_node(headId, label=head)

            if tailId not in g.nodes:
                g.add_node(tailId, label=tail)

            color = edge_colors[reltype]
            arrows = "to" if reltype not in Builder.get_bidir_rels() else None
            g.add_edge(headId, tailId, color=color, label=reltype, hoverWidth=2, arrows=arrows)

        return g


# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
