import re
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

        self.graph = None

        # with open('appendix.json', 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

    @staticmethod
    def get_bidir_rels():
        return ['hyponyms', 'synonyms', 'antonyms']
    

    def def2word(self):
        query = [
            f"SELECT {self.definitions_table}.headword head, {self.definitions_table}.partOfSpeech headPOS, {self.definitions_table}.wordId headId, {self.edge_table}.relationshipType, {self.word_table}.word tail, {self.word_table}.id tailId FROM {self.edge_table}",
            f"JOIN {self.definitions_table} ON {self.definitions_table}.id = {self.edge_table}.headDefinitionId",
            f"JOIN {self.word_table} ON {self.word_table}.id = {self.edge_table}.wordId",
        ]
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_vocab(self, category_info=True):
        from_table = f"{self.word_table}.*"
        if category_info:
            from_table = "categories.*, " + from_table
        query = [
            f"SELECT {from_table} FROM {'word_categories' if category_info else self.word_table}",
        ]
        if category_info:
            query.append(f"JOIN {self.word_table} ON {self.word_table}.id = word_categories.wordId")
            query.append(f"JOIN categories ON categories.id = word_categories.categoryId")
            
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_category_relations(self):
        query = [
            f"SELECT w.id headId, w.word head, c.id tailId, c.text tail, 'categoryOf' relationshipType FROM word_categories wc",
            f"JOIN {self.word_table} w ON w.id = wc.wordId",
            f"JOIN categories c ON c.id = wc.categoryId",
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        relations = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        relations = [dict(zip(column_names, row)) for row in cur.fetchall()]

        return relations

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
    
    def get_categories(self, category_ids=None):
        query = [
            f"SELECT * FROM categories",
        ]
        if hasattr(category_ids, '__iter__') and type(category_ids) != str:
            category_ids = [f"'{c}'" for c in category_ids]
            category_ids = ", ".join(category_ids)
            query.append(f"WHERE id IN ({category_ids})")
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_pyvis_graph(self, instance="w2w", preprocessing_callback=None, category_info=True, nodes_palette="tab10", edges_palette="tab10", **kwargs):
        self.graph = Network(**kwargs)

        if instance == "w2w":
            graph_data = self.word2word()
        elif instance == "d2w":
            graph_data = self.def2word()
        else:
            return self.graph
        

        vocab = self.get_vocab(category_info=False)
        if category_info:
            cat_relations = self.get_category_relations()
            graph_data += cat_relations
            cat_ids = [c['tailId'] for c in cat_relations]
            categories = self.get_categories(category_ids=cat_ids)
            for cat in categories:
                # cat['language'] = re.sub('^(.+):(.+)', '\g<1>', cat['text'])
                cat['language'] = "Category"
                cat['word'] = re.sub('^(.+):(.+)', '\g<2>', cat['text'])
                vocab.append(cat)

        if preprocessing_callback is None:
            preprocessing_callback = lambda x: x

        language_map = {w.get('language') for w in vocab}
        language_norm = []
        for l in language_map:
            if len(str(l)) > 3 and l not in [None, "Category"]:
                l = langcodes.find(l).language

            language_norm.append(l)
        language_map = dict(zip(language_map, language_norm))

        edge_labels = {r.get('relationshipType') for r in graph_data}

        if type(nodes_palette) == str:
            node_colors = get_colormap(language_norm, palette=nodes_palette)
        else:
            node_colors = nodes_palette

        if type(edges_palette) == str:
            edge_colors = get_colormap(edge_labels, palette=edges_palette)
        else:
            edge_colors = edges_palette



        for w in vocab:
            lang = w.get('language')
            lang = language_map[lang]
            color = node_colors.get(lang, "black")
            word = preprocessing_callback(w.get('word'))
            title = f"{word} ({lang})" if lang is not None else f"{word} (?)"
            self.graph.add_node(w.get('id'), label=word, title=title, color=color, hover=True)

        for r in graph_data:
            headId = r.get('headId')
            tailId = r.get('tailId')
            head = preprocessing_callback(r.get('head'))
            tail = preprocessing_callback(r.get('tail'))
            reltype = r.get('relationshipType')

            if headId not in self.graph.nodes:
                self.graph.add_node(headId, label=head, pos=r.get('headPOS'))

            if tailId not in self.graph.nodes:
                self.graph.add_node(tailId, label=tail, pos=r.get('tailPOS'))

            color = edge_colors[reltype]
            arrows = "to" if reltype not in Builder.get_bidir_rels() else None
            self.graph.add_edge(headId, tailId, color=color, label=reltype, hoverWidth=2, arrows=arrows)

        return self.graph

    def word2word(self):
        query = [
            f"SELECT whead.id headId, whead.word head, wtail.id tailId, wtail.word tail, {self.edge_table}.relationshipType FROM {self.edge_table}",
            f"JOIN {self.word_table} wtail ON wtail.id = {self.edge_table}.wordId",
            f"JOIN {self.definitions_table} def ON def.id = {self.edge_table}.headDefinitionId",
            f"JOIN {self.word_table} whead ON def.wordId = whead.id",
        ]
        query = "\n".join(query)
        print(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
