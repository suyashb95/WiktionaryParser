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
                 force_edge_tail_constraint=False
                ):

        self.conn = conn
        self.DEFINED_TAGS = ['proper noun']
        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

        self.graph = None
        self.vocab = None
        self.language_map = None
        self.node_ids = {}
        # with open('appendix.json', 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

    @staticmethod
    def get_bidir_rels():
        return ['hyponyms', 'synonyms', 'antonyms']
    
    def word2word(self, query_filter=None):
        query = [
            f"SELECT hdef.wordId headId, hdef.partOfSpeech headPOS, hdef.headWord head, tdef.wordId tailId, tdef.partOfSpeech tailPOS, tdef.headWord tail, {self.edge_table}.relationshipType FROM {self.edge_table}",
            f"JOIN {self.definitions_table} hdef ON hdef.id = {self.edge_table}.headDefinitionId",
            f"LEFT JOIN {self.definitions_table} tdef ON tdef.wordId = {self.edge_table}.wordId",
        ]
        where_clause = []
        if query_filter is not None:
            for k, v in query_filter.items():
                if hasattr(v, "__iter__") and type(v) != str:
                        if len(v) > 0:
                            v = ', '.join([f"'{e}'" for e in v])
                            filter_ = f"{k} IN ({v})"
                        else:
                            continue
                else:
                    filter_ = f"{k} = {v}"
                where_clause.append(filter_)
        if len(where_clause) > 0:
            where_clause = " AND ".join(where_clause)
            where_clause = "WHERE " + where_clause
            query.append(where_clause)
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def def2word(self, query_filter=None):
        query = [
            f"SELECT hdef.headword head, hdef.partOfSpeech headPOS, hdef.wordId headId, {self.edge_table}.relationshipType, tdef.headWord tail, tdef.partOfSpeech tailPOS, tdef.wordId tailId FROM {self.edge_table}",
            f"JOIN {self.definitions_table} hdef ON hdef.id = {self.edge_table}.headDefinitionId",
            f"LEFT JOIN {self.definitions_table} tdef ON tdef.wordId = {self.edge_table}.wordId"
        ]
        where_clause = []
        if query_filter is not None:
            for k, v in query_filter.items():
                if hasattr(v, "__iter__") and type(v) != str:
                        if len(v) > 0:
                            v = ', '.join([f"'{e}'" for e in v])
                            filter_ = f"{k} IN ({v})"
                        else:
                            continue
                else:
                    filter_ = f"{k} = {v}"
                where_clause.append(filter_)
        if len(where_clause) > 0:
            where_clause = " AND ".join(where_clause)
            where_clause = "WHERE " + where_clause
            query.append(where_clause)
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_vocab(self, category_info=True, partOfSpeech=False):
        from_table = f"{self.word_table}.*"
        if category_info:
            from_table = from_table + ", C.title categoryTitle, C.id categoryId"
        if partOfSpeech:
            from_table = "def.partOfSpeech, " + from_table
        query = [
            f"SELECT {from_table} FROM {'word_categories' if category_info else self.word_table}",
        ]
        if category_info:
            query.append(f"JOIN {self.word_table} ON {self.word_table}.id = word_categories.wordId")
            query.append(f"JOIN categories C ON C.id = word_categories.categoryId")

        if partOfSpeech:
            query.append(f"JOIN {self.definitions_table} def ON {self.word_table}.id = def.wordId")

            
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_category_relations(self):
        query = [
            f"SELECT w.id headId, d.partOfSpeech headPOS, w.word head, c.id tailId, c.text tail, 'categoryOf' relationshipType", 
            f"FROM word_categories wc",
            f"JOIN {self.definitions_table} d ON d.wordId = wc.wordId",
            f"JOIN {self.word_table} w ON w.id = wc.wordId",
            f"JOIN categories c ON c.id = wc.categoryId",
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        relations = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        relations = [dict(zip(column_names, row)) for row in cur.fetchall()]

        return relations
    
    def get_appendix_relations(self):
        query = [
            f"SELECT w.id headId, d.partOfSpeech headPOS, w.word head, apx.id tailId, apx.label tail, 'tagOf' relationshipType", 
            f"FROM {self.definitions_table}_apx defapx",
            f"JOIN {self.definitions_table} d ON defapx.definitionId = d.id",
            f"JOIN {self.word_table} w ON w.id = d.wordId",
            f"JOIN appendix apx ON apx.id = defapx.appendixId",
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        relations = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        relations = [dict(zip(column_names, row)) for row in cur.fetchall()]

        return relations

    def get_orphan_nodes(self):
        query = [
            f"SELECT * FROM {self.word_table}",
            "WHERE isDerived=1",
            "AND wikiUrl IS NOT NULL",
            # "LIMIT 25"
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
            if len(category_ids) > 0:
                category_ids = ", ".join(category_ids)
                query.append(f"WHERE id IN ({category_ids})")
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
    def get_appendices(self, appendix_ids=None):
        query = [
            f"SELECT * FROM appendix",
        ]
        if hasattr(appendix_ids, '__iter__') and type(appendix_ids) != str:
            appendix_ids = [f"'{c}'" for c in appendix_ids]
            appendix_ids = ", ".join(appendix_ids)
            query.append(f"WHERE id IN ({appendix_ids})")
        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        return result
    
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

        if preprocessing_callback is None:
            preprocessing_callback = lambda x: x

        data_dict = {}
        self.node_ids = {}
        
        for e in graph_data:        
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

