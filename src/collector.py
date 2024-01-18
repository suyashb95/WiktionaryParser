import json
from pathlib import Path
import re
from uu import encode
import requests
from bs4 import BeautifulSoup
import csv
import os
import tqdm
import copy
from nltk.stem import *
import itertools
import hashlib

from src.database import MySQLClient

from .utils import flatten_dict


class Collector:
    def __init__(self, conn, 
                 word_table="words", 
                 dataset_table="data", 
                 edge_table="relationships",
                 definitions_table="definitions",
                 force_edge_tail_constraint=True,
                 auto_flush_after = 10
                ):

        self.conn: MySQLClient = conn

        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

        self.batch = []
        self.auto_flush_after = auto_flush_after
        self.force_edge_tail_constraint = force_edge_tail_constraint

        self.hash_word_by = "{word} ({language})"
        self.hash_def_by = "{wordId} {pos}_{raw_text}"

        self.base_url = "https://en.wiktionary.org/"
    def reset_db(self):
        self.__create_tables()
        with open('appendix.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

        with open('category_links.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(self.__get_category_data(), indent=2, ensure_ascii=False))

    @staticmethod
    def apply_hash(text):
        # return text
        return hashlib.sha256(text.encode()).hexdigest()
    
    def __create_tables(self):
        # Define the table names
        table_names = {
            "word_table": self.word_table,
            "dataset_table": self.dataset_table,
            "definitions_table": self.definitions_table,
            "edge_table": self.edge_table,
        }

        # Load and format the SQL script from the file
        self.conn.load_sql_from_file('query.sql', **table_names)

        # Execute the formatted script (which might contain multiple queries)
        self.conn.execute()

    def __get_appendix_data(self):
        res = []
        urls = {
            "glossary": {
                "url": "https://en.wiktionary.org/wiki/Appendix:Glossary"
            },
            "ar_verbs": {
                "url": "https://en.wiktionary.org/wiki/Appendix:Arabic_verbs"
            }
        }
        for cat, v in urls.items():
            url = v.get('url')
            if url is None:
                continue
            response = requests.get(url).content
            soup = BeautifulSoup(response, 'html.parser')
            for e in soup.find_all('span', {"class":"mw-editsection"}):
                e.extract()
            sections = soup.select('.mw-parser-output')
            for section in sections:
                dl = section.select('dd, dt, p, h3')
                desc = None
                label = None
                wiki_url = None
                for e in dl:
                    if e.name in ["dd", "p"]:
                        desc = e.text.strip()
                    elif e.name in ["dt", "h3"]:
                        desc = None
                        label = e.text.strip()
                        wiki_url = e.select_one('a')
                        wiki_url = wiki_url if wiki_url is None else wiki_url.get('href')
                    
                    if None not in [desc, label]:
                        apx = {
                            "label": label,
                            "description": desc,
                            "wikiUrl": wiki_url,
                            "category": cat
                        }
                        # apx_unique_hash = '_'.join([str(apx[k]) for k in sorted(apx)])
                        apx_unique_hash = label
                        apx['id'] = Collector.apply_hash(apx_unique_hash)
                        res.append(apx)
                    
        self.conn.insert("appendix", res, ignore=True)
        return res
    
    def __get_category_data(self, lang="ar"):
        urls = {
            "set_categories": f'https://en.wiktionary.org/wiki/Category:{lang}:List_of_set_categories',
            "name_categories": f'https://en.wiktionary.org/wiki/Category:{lang}:List_of_name_categories',
            "type_categories": f'https://en.wiktionary.org/wiki/Category:{lang}:List_of_type_categories',
        }
        data = []
        for k in urls:
            url = urls[k]
            while True:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "lxml")
                #Get all links
                links = soup.select(".CategoryTreeItem>a")
                for a in links:
                    # tree_bullet = a.find_previous_sibling('span')
                    # hasSubcat = "CategoryTreeBullet" in tree_bullet.get('class')
                    a_data = {
                        "sourceList": k,
                        "id": Collector.apply_hash(a.get_text()),
                        "title": a.get("title"),
                        "text": a.get_text(),
                        "wikiUrl": a.get("href"),
                        # "hasSubcat": hasSubcat
                    }
                    data.append(a_data)

                url = soup.find("a", text="next page")
                if url is None:
                    break

                url = self.base_url + url.get('href')
        self.conn.insert("categories", data, ignore=True)
        return data

    def erase_db(self, recreate_database=False):
        if recreate_database:
            self.reset_db()
        self.conn.execute("SET FOREIGN_KEY_CHECKS = 0")
        target_tables = [
            self.definitions_table+"_apx", self.edge_table, 'word_categories', "examples",
            # 'categories', 'appendix',
            self.definitions_table, self.dataset_table, self.word_table
        ]
        target_tables = tqdm.tqdm(target_tables, leave=False)
        for table in target_tables:
            target_tables.set_description_str(f'Truncating {table}')
            self.conn.execute(f"TRUNCATE TABLE {table}")
            self.conn.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
        self.conn.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    @staticmethod
    def adapt_csv_dataset(dataset_file: os.PathLike, delimiter=',', header=0, dataset_name=None, text_col=0, label_col=-1, task=None):
        data = []
        with open(dataset_file, "r", encoding="utf8") as csv_file:
            rows = csv.reader(csv_file, delimiter=delimiter)
            for i, row in enumerate(rows):
                if i == header:
                    continue
                text, label = row[text_col], row[label_col]
                data.append(dict(text=text, label=label, dataset_name=dataset_name, task=task))
        return data
    
    def existing_wikiUrls(self):
        res = self.conn.read(fields="wikiUrl", collection_name=self.word_table)
        return {e.get('wikiUrl') for e in res}
    
    def insert_data(self, dataset, dataset_name=None, task=None):
        task = task if task is not None else 'NULL'
        dataset_name = dataset_name if dataset_name is not None else 'NULL'
        # dataset = dataset[:5]
        rows = []
        for e in tqdm.tqdm(dataset, desc=f"Inserting database: {dataset_name}", leave=False):
            row = copy.copy(e)
            row.update({"dataset_name": dataset_name, "task": task})
            row = {k: "NULL" if v is None else v for k, v in row.items()}
            rows.append(row)
        
        self.conn.insert(self.dataset_table, rows)

    def get_datasets(self, dataset_name=None, task=None):
        conditions = {
            "dataset_name": dataset_name,
            "task": task
        }
        conditions = {k: v for k, v in conditions.items() if v is not None}
        return self.conn.read(self.dataset_table, conditions)
    # Following code made with ChatGPT Free (Needs to be checked)
 
    def process_fetched_relationships(self, element, word_id, hash_maxlen=-1):
        related_words = []
        for rw in element.get("relatedWords", []):
            rw['wordId'] = word_id
            rw['pos'] = element.get("partOfSpeech")
            rw_list = flatten_dict(rw)
            for i in range(len(rw_list)):
                rw_list[i].update(rw_list[i].get("words", {}))
                lang = rw_list[i].get('language')
                wikiUrl = rw_list[i].get('wikiUrl')
                if lang is None and wikiUrl is not None:
                    lang = re.search('#\w+$', wikiUrl)
                    if lang is not None:
                        lang = lang.group(0)
                        lang = re.sub('#|_', ' ', lang.lower()).strip()

                rw_list[i]['language'] = lang

                rw_list[i]['raw_text'] = rw_list[i].pop('def_text', None)
                #gugus
                # headDefinitionId = Collector.apply_hash(self.hash_def_by.format(**rw_list[i]))
                # rw_list[i]['headDefinitionId'] = headDefinitionId
                rw_list[i]['word'] = rw_list[i].pop('words')
                rw_list[i]['wordId'] = Collector.apply_hash(self.hash_word_by.format(**rw_list[i]))
                
            related_words += rw_list
     
        return related_words

    def process_fetched_definition(self, element, word_id, hash_maxlen=-1):
        definition = {
            "wordId": word_id, #FOREIGN KEY
            "partOfSpeech": element.get("partOfSpeech"),
            "text": element.get("text", []),
        }
        appendices = []
        mentions = []
        categories = []
        examples = []
        hashes = {}
        #Add definitions
        definition = flatten_dict(definition)
        for i in range(len(definition)):
            definition[i].update(definition[i].get("text", {}))
            definition[i]['pos'] = definition[i].get('pos', element.get('partOfSpeech'))
            #Get a unique hash that encodes word, its POS and its explanation (to disambiguate verbal form from nominal form)
            unique_w_hash = self.hash_def_by.format(**definition[i])
            unique_w_hash = Collector.apply_hash(unique_w_hash)
            
            for k_ in ["raw_text"]:
                definition[i].pop(k_, None)

            #Isolate appendix in its own table
            appendix = definition[i].pop('appendix_tags', [])
            appendix = [a.lower().strip() for a in appendix]
            appendix = [a.replace(u"\xa0", ' ') for a in appendix]
            
            appendix = {
                "appendixId": [
                    Collector.apply_hash(e) for e in appendix
                ], #FOREIGN KEY
                "appendixLabel": appendix
            }
            appendix = flatten_dict(appendix)
            mentions_ = definition[i].pop("mentions", [])
            def_examples = definition[i].pop('examples', [])

            definition[i]['id'] = unique_w_hash #PRIMARY KEY

            for m in range(len(mentions_)):
                mentions_[m]['definitionId'] = unique_w_hash

            for a in range(len(appendix)):
                appendix[a]['definitionId'] = unique_w_hash
            
            for e in range(len(def_examples)):
                def_examples[e]['definitionId'] = unique_w_hash

            def_id = definition[i].get('def_k')
            hashes[def_id] = hashes.get(def_id, []) + [unique_w_hash]
            appendices += appendix
            mentions += mentions_
            examples += def_examples

            # definition[i] = {k: definition[i][k] for k in sorted(definition[i].keys(), key=lambda x: x!="id")}


        return definition, appendices, mentions, categories, examples, hashes
        
    def save_word(self, fetched_data, save_to_db=False, save_orphan=True, save_mentions=True):
        hash_maxlen = 48
        related_words = []
        orph_nodes = []
        definitions = []
        appendices = []
        words = []
        examples = []
        categories = []

        for row in fetched_data:
            word = {
                k: row.get(k) for k in ['id', 'etymology', 'language', "query", 'word', 'wikiUrl', 'isDerived']
            }
            
            word_str = word['word']
            word_id = Collector.apply_hash(self.hash_word_by.format(**word))
            word['wikiUrl'] = word['wikiUrl'] if word['wikiUrl'] is not None else f"/wiki/{word_str}"
            #Row may appear with its actual id if the 
            if word['id'] is None:
                word['id'] = word_id
            unshakled_word_str = re.sub(r'[\u064B-\u0655]', '', word_str)
            word['word'] = re.sub('\W|_', ' ', unshakled_word_str)
            word['isDerived'] = 0
            words.append(word)
                        
            #Isolate categories in their own table
            categories_ = row.pop('categories', [])
            categories_ = {
                "categoryId": [
                    Collector.apply_hash(e) for e in categories_
                ], #FOREIGN KEY,
                "categoryLabel": categories_
            }
            categories_['wordId'] = word_id
            categories_ = flatten_dict(categories_)
            categories += categories_

            for element in row.get("definitions", []):
                element['language'] = word['language']

                # Related words
                relations = self.process_fetched_relationships(element, word_id, hash_maxlen=hash_maxlen)
                
                #Definitions
                definition, appendix, mentions, word_categories, w_examples \
                    , hashes  = self.process_fetched_definition(element, word_id, hash_maxlen=hash_maxlen)

                for i in range(len(relations)):
                    def_k = relations[i].get('def_k')
                    if def_k is None:
                        continue
                    headDefinitionId = hashes.get(def_k, [None])[-1]
                    relations[i]['headDefinitionId'] = headDefinitionId

                #Newly discovered words (From relationships)
                if save_orphan:
                    for r in relations:
                        onode = {}
                        onode['word'] = r.pop('word')
                        onode['wikiUrl'] = r.get('wikiUrl')
                        onode['query'] = word_str
                        onode['etymology'] = None
                        onode['language'] = word.get("language")
                        onode['id'] = Collector.apply_hash(self.hash_word_by.format(**onode))
                        onode['isDerived'] = 1
                        orph_nodes.append(onode)

                #Newly discovered words (From mentions)
                if save_mentions:
                    for m in mentions:
                        mnode = copy.deepcopy(m)
                        mnode.update({
                            "id": Collector.apply_hash(self.hash_word_by.format(**m)),
                            "query": word.get("word"),
                            "etymology": None,
                        })
                        mnode_def_id = mnode.pop('definitionId')
                        new_rel = {
                            "relationshipType": "mention",
                            "wordId": mnode['id'],
                            "headDefinitionId": mnode_def_id,
                            # "word": mnode['word'],
                        }
                        orph_nodes.append(mnode)
                        relations.append(new_rel)
                
                #Add to stack
                definitions += definition
                appendices += appendix
                related_words += relations
                categories += word_categories
                examples += w_examples

        definitions = dict((d['id'], d) for d in definitions)
        definitions = list(definitions.values())
        
        categories = {(e['categoryId'], e['wordId']): e for e in categories}
        categories = list(categories.values())
        related_words = sorted(related_words, key=lambda x:x.get('wordId'))
        res = {
            "words": words, 
            "definitions": definitions,
            "related_words": related_words,
            "appendices": appendices,
            "orph_nodes": orph_nodes,
            "categories": categories,
            "examples": examples
        } 
        if save_to_db:
            # self.save_word_data(**res)
            if self.auto_flush_after > 0 :
                self.batch.append(res)
                if self.auto_flush_after <= len(self.batch):
                    self.flush()

        return res #fetched_data #related_words
    
    def flush(self):
        res = {}
        for b in tqdm.tqdm(self.batch, position=0, leave=False):
            for k in b:
                res[k] = res.get(k, []) + b[k]
        print('Flushing...', end='')
        updated_rows = self.update_word_data(**res)
        inserted_rows = self.insert_word_data(**res)
        affected_rows = {"insert": inserted_rows, "update": updated_rows}
        print(affected_rows)
        self.batch = []

    def update_word_data(self, words=[],  orph_nodes=[], **kwargs):
        # Updating to database
        updated_rows = {}
        derivedUpd = self.conn.update(self.word_table, data=words, conditions={"id": "%(id)s"}, ignore=True, isDerived=0)
        underivedUpd = self.conn.update(self.word_table, data=orph_nodes, conditions={"id": "%(id)s"}, ignore=True, isDerived=1)
        updated_rows[self.word_table] = derivedUpd + underivedUpd
        updated_rows = {k: sum(v) for k, v in updated_rows.items()}
        return updated_rows

    def insert_word_data(self, words=[], definitions=[], related_words=[], appendices=[], orph_nodes=[], categories=[], examples=[], insert=True, update=True):
        # Inserting into database
        inserted_rows = {}
        inserted_rows[self.word_table] = self.conn.insert(self.word_table, words, ignore=True)
        inserted_rows[self.word_table] += self.conn.insert(self.word_table, orph_nodes, ignore=True)
        
        inserted_rows[self.definitions_table] = self.conn.insert(self.definitions_table, definitions, ignore=True)
        inserted_rows["examples"] = self.conn.insert("examples", examples, ignore=True)
        
        inserted_rows[f"{self.definitions_table}_apx"] = self.conn.insert(f"{self.definitions_table}_apx", appendices, ignore=True)
        inserted_rows["word_categories"] = self.conn.insert("word_categories", categories, ignore=True)
        inserted_rows[self.edge_table] = self.conn.insert(self.edge_table, related_words, ignore=True)

        inserted_rows = {k: sum(v) for k, v in inserted_rows.items()}
        return inserted_rows
        

    
    def export_to_csv(self, path, encoding="utf8", sep=","):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        tables = self.conn.get_table_names()
        for table in tables:
            result = self.conn.read(table)
            keys = result[0].keys()
            
            with open(os.path.join(path, f"{table}.csv"), "w", encoding=encoding, newline='') as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(result)



# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
