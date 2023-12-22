from collections import Counter
import os

os.environ['DGLBACKEND'] = "pytorch"
import dgl
import torch
import re
import os
from nltk.stem import *


class GraphBuilder:
    def __init__(self, conn, 
                 word_table="words", 
                 dataset_table="data", 
                 edge_table="relationships",
                 definitions_table="definitions",
                ):

        self.conn = conn
        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

        self.graph = None
        self.vocab = None
        self.language_map = None
        self.node_ids = {}

    @staticmethod
    def get_bidir_rels():
        return ['hyponyms', 'synonyms', 'antonyms']
    
    def word2word(self, query_filter=None):
        joins = [
            (self.definitions_table, f"{self.definitions_table}.id = {self.edge_table}.headDefinitionId"),
            (self.definitions_table, f"{self.definitions_table}.wordId = {self.edge_table}.wordId", 'LEFT')
        ]
        fields = f"hdef.wordId as headId, hdef.partOfSpeech as headPOS, hdef.headWord as head, " \
                 f"tdef.wordId as tailId, tdef.partOfSpeech as tailPOS, tdef.headWord as tail, " \
                 f"{self.edge_table}.relationshipType"

        # Format where clause based on query_filter
        where_clause = {}
        if query_filter is not None:
            for k, v in query_filter.items():
                if isinstance(v, (list, tuple)):
                    where_clause[k] = "(" + ", ".join([f"'{e}'" for e in v]) + ")"
                else:
                    where_clause[k] = v

        result = self.conn.read(
            collection_name=self.edge_table,
            fields=fields,
            joins=joins,
            conditions=where_clause
        )

        return result
    
    def def2word(self, query_filter=None):
        joins = [
            (self.definitions_table, f"{self.definitions_table}.id = {self.edge_table}.headDefinitionId"),
            (self.definitions_table, f"{self.definitions_table}.wordId = {self.edge_table}.wordId", 'LEFT')
        ]
        fields = f"hdef.headword as head, hdef.partOfSpeech as headPOS, hdef.wordId as headId, " \
                 f"{self.edge_table}.relationshipType, tdef.headWord as tail, tdef.partOfSpeech as tailPOS, tdef.wordId as tailId"

        # Format where clause based on query_filter
        where_clause = {}
        if query_filter is not None:
            for k, v in query_filter.items():
                if isinstance(v, (list, tuple)):
                    where_clause[k] = "(" + ", ".join([f"'{e}'" for e in v]) + ")"
                else:
                    where_clause[k] = v

        result = self.conn.read(
            collection_name=self.edge_table,
            fields=fields,
            joins=joins,
            conditions=where_clause
        )

        return result
    
    def get_vocab(self, category_info=True, partOfSpeech=False):
        fields = f"{self.word_table}.*"
        joins = []

        if category_info:
            fields += ", C.title as categoryTitle, C.id as categoryId"
            joins.append(("word_categories", f"{self.word_table}.id = word_categories.wordId"))
            joins.append(("categories C", "C.id = word_categories.categoryId"))

        if partOfSpeech:
            if not category_info:
                # If category_info is False, we need to ensure the correct FROM table
                joins.append((self.definitions_table, f"{self.word_table}.id = {self.definitions_table}.wordId"))
            fields = "def.partOfSpeech, " + fields

        collection_name = 'word_categories' if category_info else self.word_table
        result = self.conn.read(
            collection_name=collection_name,
            fields=fields,
            joins=joins
        )

        return result
    
    def get_category_relations(self):
        fields = "w.id as headId, d.partOfSpeech as headPOS, w.word as head, " \
                 "c.id as tailId, c.text as tail, 'categoryOf' as relationshipType"
        joins = [
            (self.definitions_table, "d.wordId = word_categories.wordId"),
            (self.word_table, "w.id = word_categories.wordId"),
            ("categories c", "c.id = word_categories.categoryId")
        ]

        result = self.conn.read(
            collection_name="word_categories",
            fields=fields,
            joins=joins
        )

        return result
    
    def get_appendix_relations(self):
        fields = "w.id as headId, d.partOfSpeech as headPOS, w.word as head, " \
                 "apx.id as tailId, apx.label as tail, 'tagOf' as relationshipType"
        joins = [
            (f"{self.definitions_table} d", "defapx.definitionId = d.id"),
            (self.word_table, "w.id = d.wordId"),
            ("appendix apx", "apx.id = defapx.appendixId")
        ]

        result = self.conn.read(
            collection_name=f"{self.definitions_table}_apx defapx",
            fields=fields,
            joins=joins
        )

        return result

    def get_orphan_nodes(self):
        conditions = {
            "isDerived": 1,
            "wikiUrl": "IS NOT NULL"
        }

        result = self.conn.read(
            collection_name=self.word_table,
            conditions=conditions
        )

        return result
    
    def get_dataset(self, dataset_name=None, task=None):
        conditions = {}
        if dataset_name is not None:
            conditions["dataset_name"] = dataset_name
        if task is not None:
            conditions["task"] = task

        # Adjust the conditions dictionary to handle cases where values are lists
        for key, value in list(conditions.items()):
            if isinstance(value, (list, tuple)):
                conditions[key + " IN"] = "(" + ", ".join([f"'{e}'" for e in value]) + ")"
                del conditions[key]

        result = self.conn.read(
            collection_name=self.dataset_table,
            conditions=conditions
        )

        return result
    
    def get_categories(self, category_ids=None):
        conditions = {}
        if category_ids is not None:
            if isinstance(category_ids, (list, tuple)):
                # Convert list to a format suitable for SQL IN clause
                conditions["id IN"] = "(" + ", ".join([f"'{c}'" for c in category_ids]) + ")"
            else:
                # Single category ID
                conditions["id"] = category_ids

        result = self.conn.read(
            collection_name="categories",
            conditions=conditions
        )

        return result
    
    def get_appendices(self, appendix_ids=None):
        conditions = {}
        if appendix_ids is not None:
            if isinstance(appendix_ids, (list, tuple)):
                # Convert list to a format suitable for SQL IN clause
                conditions["id IN"] = "(" + ", ".join([f"'{id}'" for id in appendix_ids]) + ")"
            else:
                # Single appendix ID
                conditions["id"] = appendix_ids

        result = self.conn.read(
            collection_name="appendix",
            conditions=conditions
        )

        return result
    
    #### FOLLOWING METHODS DO NOT MAKE DIRECT REQUESTS TO DATABASE
    
    def build_graph_vocab(self, category_info=False, appendix_info=False):
        category_rels = []
        appendix_rels = []
        if self.vocab is None:
            self.vocab = self.get_vocab(partOfSpeech=True, category_info=False)
        vocab = self.vocab

        if category_info:
            cat_relations = self.get_category_relations()
            category_rels += cat_relations
            cat_ids = [c['tailId'] for c in cat_relations]
            categories = self.get_categories(category_ids=cat_ids)
            for cat in categories:
                # cat['language'] = re.sub('^(.+):(.+)', '\g<1>', cat['text'])
                cat['language'] = "Category"
                cat['word'] = re.sub('^(.+):(.+)', '\g<2>', cat['text'])
                vocab.append(cat)

        if appendix_info:
            apx_relations = self.get_appendix_relations()
            appendix_rels += apx_relations
            apx_ids = [a['tailId'] for a in apx_relations]
            appendices = self.get_appendices(appendix_ids=apx_ids)
            for apx in appendices:
                apx['language'] = "Tag"
                apx['word'] = apx['label']
                vocab.append(apx)
        
        self.vocab = {w['id']: w for w in vocab}
        return category_rels, appendix_rels

    def __process_graph_edges(self, graph_data, category_info=True, appendix_info=False, use_pos=True, g_key=('token', 'token')):
        category_rels, appendix_rels = self.build_graph_vocab(category_info=category_info, appendix_info=appendix_info)
        for e in graph_data:
            if use_pos:
                e['tailPOS'] = e['tailPOS'] if e.get('tailPOS') is not None else "orphan_"+g_key[-1]
                e["headType"], e["tailType"] = e['headPOS'], e['tailPOS']
            else:
                e["headType"], e["tailType"] = g_key
        
                
        for e in category_rels:
            if use_pos:
                e["headType"], e["tailType"] = e['headPOS'], "category"
            else:
                e["headType"], e["tailType"] = g_key[0], "category"

                
        for e in appendix_rels:
            if use_pos:
                e["headType"], e["tailType"] = e['headPOS'], "tag"
            else:
                e["headType"], e["tailType"] = g_key[0], "tag"

        graph_data += category_rels
        graph_data += appendix_rels

        return graph_data
    

    def build_graph(self, instance="w2w", query_filter=None, preprocessing_callback=None, category_info=True, appendix_info=False, use_pos=True, **kwargs):
        instance = instance.lower()
        if instance == "w2w":
            graph_data = self.word2word(query_filter=query_filter)
            g_key = ('word', 'word')
        elif instance == "d2w":
            graph_data = self.def2word(query_filter=query_filter)
            g_key = ('definition', 'word')
        else:
            return self.graph

        graph_edges = self.__process_graph_edges(graph_data, category_info=category_info, appendix_info=appendix_info, use_pos=use_pos, g_key=g_key)

        if preprocessing_callback is None:
            preprocessing_callback = lambda x: x

        data_dict = {}
        self.node_ids = {}
        
        for e in graph_edges:        
            reltype = e['relationshipType']
            k = (e["headType"], reltype, e["tailType"])
            #If this node type doesn't exist, create an empty list
            self.node_ids[e["headType"]] = self.node_ids.get(e["headType"], [])
            self.node_ids[e["tailType"]] = self.node_ids.get(e["tailType"], [])

            #If node id appears for the first time, append it to node list
            if e['headId'] not in self.node_ids[e["headType"]]:
                self.node_ids[e["headType"]].append(e['headId'])
            
            if e['tailId'] not in self.node_ids[e["tailType"]]:
                self.node_ids[e["tailType"]].append(e['tailId'])

            #If this relationship type doesn't exist, create an empty list
            data_dict[k] = data_dict.get(k, [])


            head = self.node_ids[e["headType"]].index(e['headId'])
            tail = self.node_ids[e["tailType"]].index(e['tailId'])

            edge = tuple([head, tail])
            data_dict[k].append(edge)

        data_dict = {k: Counter(v) for k, v in data_dict.items()}
        g_edgelist = {k: list(v.keys()) for k, v in data_dict.items()}
        g_edgeweights = {k: torch.tensor([c/sum(v.values()) for c in v.values()]) for k, v in data_dict.items()}
        self.graph = dgl.heterograph(g_edgelist)
        self.graph.edata['weights'] = g_edgeweights
        return self.graph

