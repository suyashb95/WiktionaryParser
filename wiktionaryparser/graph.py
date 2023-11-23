from collections import Counter
from copy import copy, deepcopy
import os

os.environ['DGLBACKEND'] = "pytorch"
import dgl
import torch
import torch.nn.functional as F
import re
from pyvis.network import Network
import langcodes
import os
from nltk.stem import *

from wiktionaryparser.utils import flatten_dict, get_colormap
from wiktionaryparser.feature_extraction import FeatureExtractor


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
        self.node_ids = {}
        # with open('appendix.json', 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

    @staticmethod
    def get_bidir_rels():
        return ['hyponyms', 'synonyms', 'antonyms']
    
    def word2word(self, query_filter=None):
        query = [
            f"SELECT whead.id headId, whead.word head, wtail.id tailId, wtail.word tail, {self.edge_table}.relationshipType FROM {self.edge_table}",
            f"JOIN {self.word_table} wtail ON wtail.id = {self.edge_table}.wordId",
            f"JOIN {self.definitions_table} def ON def.id = {self.edge_table}.headDefinitionId",
            f"JOIN {self.word_table} whead ON def.wordId = whead.id",
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
            f"SELECT def.headword head, def.partOfSpeech headPOS, def.wordId headId, {self.edge_table}.relationshipType, wtail.word tail, wtail.id tailId FROM {self.edge_table}",
            f"JOIN {self.definitions_table} def ON def.id = {self.edge_table}.headDefinitionId",
            f"JOIN {self.word_table} wtail ON wtail.id = {self.edge_table}.wordId",
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
            from_table = "categories.*, " + from_table
        if partOfSpeech:
            from_table = "def.partOfSpeech, " + from_table
        query = [
            f"SELECT {from_table} FROM {'word_categories' if category_info else self.word_table}",
        ]
        if category_info:
            query.append(f"JOIN {self.word_table} ON {self.word_table}.id = word_categories.wordId")
            query.append(f"JOIN categories ON categories.id = word_categories.categoryId")

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
    
    def get_appendix_relations(self):
        query = [
            f"SELECT w.id headId, w.word head, apx.id tailId, apx.label tail, 'tagOf' relationshipType FROM {self.definitions_table}_apx defapx",
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
    
    def build_graph_vocab(self, category_info=False, appendix_info=False):
        category_rels = []
        appendix_rels = []
        if self.vocab is None:
            self.vocab = self.get_vocab(partOfSpeech=True)
        vocab = self.vocab

        if appendix_info:
            apx_relations = self.get_appendix_relations()
            appendix_rels += apx_relations
            apx_ids = [a['tailId'] for a in apx_relations]
            appendices = self.get_categories(category_ids=apx_ids)
            for apx in appendices:
                apx['language'] = "Tag"
                apx['word'] = apx['text']
                vocab.append(apx)

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
        
        return vocab, category_rels, appendix_rels

    def build_graph(self, instance="w2w", query_filter=None, preprocessing_callback=None, category_info=True, appendix_info=False, nodes_palette="tab10", edges_palette="tab10", **kwargs):
        self.graph = Network(**kwargs)
        instance = instance.lower()
        if instance == "w2w":
            graph_data = self.word2word(query_filter=query_filter)
        elif instance == "d2w":
            graph_data = self.def2word(query_filter=query_filter)
        else:
            return self.graph
        
        vocab, category_rels, appendix_rels = self.build_graph_vocab(category_info=category_info, appendix_info=appendix_info)
        graph_data += category_rels
        graph_data += appendix_rels

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
            arrows = "to" if reltype not in GraphBuilder.get_bidir_rels() else None
            self.graph.add_edge(headId, tailId, color=color, label=reltype, hoverWidth=2, arrows=arrows)

        return self.graph

    def get_reltype_counts(self):
        query = [
            f"SELECT rel.relationshipType, COUNT(*) count FROM {self.edge_table} rel",
            f"GROUP BY rel.relationshipType"
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        count = {}
        for r in result:
            k = r.get('relationshipType')
            count[k] = count.get(k, 0) + r.get('count', 0)
        return count
    
    def get_pos_counts(self):
        query = [
            f"SELECT def.partOfSpeech, COUNT(*) count FROM {self.definitions_table} def",
            f"GROUP BY def.partOfSpeech"
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        count = {}
        for r in result:
            k = r.get('partOfSpeech')
            count[k] = count.get(k, 0) + r.get('count', 0)
        return count
    
    def word_pos(self):
        query = [
            f"SELECT def.partOfSpeech, w.id FROM {self.definitions_table} def",
            f"JOIN {self.word_table} w ON def.wordId = w.id"
        ]

        query = "\n".join(query)
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]
        pos_tags = {}
        for r in result:
            k = r.get('id')
            if k not in pos_tags:
                pos_tags[k] = []
            pos_tags[k].append(r.get('partOfSpeech'))
        pos_tags = {k: Counter(pos_tags[k]) for k in pos_tags}
        pos_tags = {k: {t: p/sum(pos_tags[k].values()) for t, p in pos_tags[k].items()} for k in pos_tags}
        return pos_tags
            
    def initialize_node_mappings(self):
        nodes = {node['id']: node for node in self.graph.nodes}
        node_ids = {}
        self.node_ids = {}
        for i, node_id in enumerate(nodes):
            node_ids[node_id] = i
            self.node_ids[i] = node_id

        return node_ids
    
    def initialize_edge_mappings(self):
        edges = {edge['label']: edge for edge in self.graph.edges}
        edge_ids = {}
        for i, edge_id in enumerate(edges):
            edge_ids[edge_id] = i

        return edge_ids
    
    def get_homo_graph(self, instance, category_info=False, appendix_info=False):
        if self.graph is None:
            self.build_graph(instance=instance, category_info=category_info, appendix_info=appendix_info)
        nodes = self.initialize_node_mappings()
        edges = self.initialize_edge_mappings()

        edges_src = []
        edges_dst = []
        edges_attrs = {
            "rel": [],
            "polar": [],
        }
        node_attrs = {
            k: {nodes.get(v['id']): v.get(k) for v in self.vocab}
            for k in ['sourceList', 'partOfSpeech']
        }
        for k in node_attrs:
            v = {node: None for node in nodes.values()}
            v.update(node_attrs[k])
            node_attrs[k] = v
        
        for e in self.graph.edges:
            edges_src.append(nodes[e.get('from')])
            edges_dst.append(nodes[e.get('to')])
            edges_attrs['rel'].append(edges[e.get('label')])
        
        g = dgl.graph((edges_src, edges_dst))
        
        for k in node_attrs:
            node_attrs[k] = torch.ones(len(node_attrs[k]), len(set(node_attrs[k].values())))
            g.ndata[k] = node_attrs[k]
            
        for k in edges_attrs:
            edges_attrs[k] = torch.tensor(edges_attrs[k])
            print(edges_attrs[k])
            g.edata[k] = F.one_hot(edges_attrs[k], num_classes=len(set(edges_attrs[k])))
        
        return g
    
    def get_hetero_graph(self, instance, category_info=False, appendix_info=False, default_ntype="word"):
        if self.graph is None:
            self.build_graph(instance=instance, category_info=category_info, appendix_info=appendix_info)
        nodes = self.initialize_node_mappings()
        node_types = {v.get('id'): v.get('partOfSpeech') for v in self.vocab if v.get('partOfSpeech') is not None}
        data_dict = {}
        
        for edge in self.graph.edges:
            edge_src = edge['from']
            edge_dst = edge['to']
            edge_rel = edge['label']
            edge_src_type = node_types.get(edge_src, default_ntype)
            edge_dst_type = node_types.get(edge_dst, default_ntype)

            rel = (nodes.get(edge_src), nodes.get(edge_dst))

            edge_category = (edge_src_type, edge_rel, edge_dst_type)

            data_dict[edge_category] = data_dict.get(edge_category, [])
            data_dict[edge_category].append(rel)
            
        return data_dict


