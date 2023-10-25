import json
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
from wiktionaryparser.utils import flatten_dict


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

    def word2word(self):
        query = [
            f"SELECT {self.edge_table}.wordId head, {self.edge_table}.relationshipType, {self.definitions_table}.wordId tail FROM {self.edge_table}",
            f"JOIN {self.definitions_table} ON {self.definitions_table}.id = {self.edge_table}.headDefinitionId"
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
            "WHERE wikiUrl IS NOT NULL AND etymology IS NULL",
            "LIMIT 10"
        ]
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
