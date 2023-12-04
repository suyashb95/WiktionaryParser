import json
import re
import requests
from bs4 import BeautifulSoup
import csv
import os
import tqdm
import copy
from nltk.stem import *
import itertools
import hashlib

from wiktionaryparser.core import WiktionaryParser 
from wiktionaryparser.utils import flatten_dict


class Collector:
    def __init__(self, conn, 
                 word_table="words", 
                 dataset_table="data", 
                 edge_table="relationships",
                 definitions_table="definitions",
                 force_edge_tail_constraint=True
                ):

        self.conn = conn

        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

        self.force_edge_tail_constraint = force_edge_tail_constraint

        self.base_url = "https://en.wiktionary.org/"
        self.__create_tables()
        if not True:
            with open('appendix.json', 'w', encoding='utf8') as f:
                f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

            with open('category_links.json', 'w', encoding='utf8') as f:
                f.write(json.dumps(self.__get_category_data(), indent=2, ensure_ascii=False))

    def __apply_hash(self, s):
        return hashlib.sha256(s.encode()).hexdigest()
    
    def __create_tables(self):
        table_names = {
            "word_table": self.word_table,
            "dataset_table": self.dataset_table,
            "definitions_table": self.definitions_table,
            "edge_table": self.edge_table,
        }
        cur = self.conn.cursor()
        with open('query.sql', 'r') as f:
            query = f.read()
        query = query.format(**table_names).split(';')
        for q in query:
            q = q.strip()
            if len(q) > 0:
                cur.execute(q+";")
        self.conn.commit()

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
                        apx['id'] = self.__apply_hash(apx_unique_hash)
                        res.append(apx)
                    
        cur = self.conn.cursor()
        cur.executemany("INSERT IGNORE INTO appendix (id, label, description, category, wikiUrl) VALUES (%(id)s, %(label)s, %(description)s, %(category)s, %(wikiUrl)s) ", res)
        self.conn.commit()
        return res
    
    
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
    
    def erase_db(self):
        cur = self.conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in [
            self.definitions_table+"_apx", self.edge_table, 'word_categories', "examples",
            'categories', self.definitions_table, self.dataset_table, self.word_table
            ]:
            cur.execute(f"TRUNCATE TABLE {table}")
            cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    def insert_data(self, dataset, dataset_name=None, task=None):
        task = task if task is not None else 'NULL'
        dataset_name = dataset_name if dataset_name is not None else 'NULL'
        cur = self.conn.cursor()
        for e in tqdm.tqdm(dataset, desc=f"Inserting database: {dataset_name}", leave=False):
            row = copy.copy(e)
            row.update({"dataset_name": dataset_name, "task": task})
            row = {k: "NULL" if v is None else v for k, v in row.items()}

            char_trans = str.maketrans({
                "\\": "/",
                "'": "\\'"
            })
            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in row.keys())
            values = ', '.join("'" + str(x).translate(char_trans) + "'" for x in row.values())
            query = "INSERT INTO %s ( %s ) VALUES ( %s );" % (self.dataset_table, columns, values)

            try:
                cur.execute(query)
            except Exception as err:
                # print('\n\n'+query+'\n\n')
                raise(err)
                break    
        self.conn.commit()

    def insert_dataset(self, path):
        dataset_name = path.split('/')[-1].replace('.csv', '')
        file_rows = self.coll.adapt_csv_dataset(path, dataset_name=dataset_name)
        self.coll.insert_data(file_rows, dataset_name=dataset_name, task="Sentiment Analysis")

    def process_fetched_relationships(self, element, word_id, hash_maxlen=-1):
        related_words = []
        for rw in element.get("relatedWords", []):
            rw['wordId'] = word_id
            rw['pos'] = element.get("partOfSpeech")
            rw_list = flatten_dict(rw)
            for i in range(len(rw_list)):
                rw_list[i].update(rw_list[i].get("words", {}))
                def_hash = f"{rw_list[i].get('wordId')}_{rw_list[i].get('pos')}_{rw_list[i].get('def_text')[:hash_maxlen]}"
                def_hash = self.__apply_hash(def_hash)
                rw_list[i]['def_hash'] = def_hash
                rw_list[i]['word'] = rw_list[i].pop('words')
                rw_list[i]['wordId'] = self.__apply_hash(rw_list[i]['word'])

                for k in ['pos', 'def_text']:
                    if k in rw_list[i]:
                        del rw_list[i][k]
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
        #Add definitions
        definition = flatten_dict(definition)
        for i in range(len(definition)):
            definition[i].update(definition[i].get("text", {}))
            # for k_ in ["examples"]:
            #     if k_ in definition[i]:
            #         definition[i].pop(k_)
                    
            #Get a unique hash that encodes word, its POS and its explanation (to disambiguate verbal form from nominal form)
            unique_w_hash = f"{definition[i].get('wordId')}_{definition[i].get('partOfSpeech')}_{definition[i].get('raw_text')[:hash_maxlen]}"
            unique_w_hash = self.__apply_hash(unique_w_hash)
            definition[i]['definitionId'] = unique_w_hash #PRIMARY KEY

            #Isolate appendix in its own table
            appendix = definition[i].pop('appendix_tags', [])
            appendix = [a.lower().strip() for a in appendix]
            appendix = [a.replace(u"\xa0", ' ') for a in appendix]
            
            appendix = {
                "appendixId": [
                    self.__apply_hash(e) for e in appendix
                ] #FOREIGN KEY
            }
            appendix['definitionId'] = unique_w_hash
            appendix = flatten_dict(appendix)
            appendices += appendix

            #Isolate mentions their its own table
            mentions_ = definition[i].pop("mentions", [])
            for m in range(len(mentions_)):
                mentions_[m]['definitionId'] = unique_w_hash
            
            mentions += mentions_
            def_examples = definition[i].pop('examples', [])
            for e in range(len(def_examples)):
                def_examples[e]['definitionId'] = unique_w_hash

            examples += def_examples


        return definition, appendices, mentions, categories, examples
        
    def save_word(self, fetched_data, save_to_db=False, save_orphan=True):
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
            word_id = self.__apply_hash(word_str)
            word['wikiUrl'] = word['wikiUrl'] if word['wikiUrl'] is not None else f"/wiki/{word_str}"
            #Row may appear with its actual id if the 
            if word['id'] is None:
                word['id'] = word_id
            word['word'] = re.sub('\W|_', ' ', word_str)
            words.append(word)
                        
            #Isolate categories in their own table
            categories_ = row.pop('categories', [])
            categories_ = {
                "categoryId": [
                    self.__apply_hash(e) for e in categories_
                ] #FOREIGN KEY,
            }
            categories_['wordId'] = word_id
            categories_ = flatten_dict(categories_)
            categories += categories_

            for element in row.get("definitions", []):
                # Related words
                relations = self.process_fetched_relationships(element, word_id, hash_maxlen=hash_maxlen)
                
                #Definitions
                definition, appendix, mentions, word_categories, w_examples = self.process_fetched_definition(element, word_id, hash_maxlen=hash_maxlen)

                #Newly discovered words (From relationships)
                if save_orphan:
                    for r in relations:
                        onode = {}
                        onode['word'] = r.get('word')
                        onode['wikiUrl'] = r.get('wikiUrl')
                        onode['id'] = self.__apply_hash(onode['word'])
                        onode['query'] = word_str
                        onode['etymology'] = None
                        onode['language'] = word.get("language")
                        
                        orph_nodes.append(onode)

                #Newly discovered words (From mentions)
                if save_orphan:
                    for m in mentions:
                        mnode = copy.deepcopy(m)
                        mnode.update({
                            "id": self.__apply_hash(m.get('word')),
                            "query": word.get("word"),
                            "etymology": None
                        })
                        mnode_def_id = mnode.pop('definitionId')
                        new_rel = {
                            "relationshipType": "mention",
                            "wordId": mnode['id'],
                            "def_hash": mnode_def_id,
                            "word": mnode['word']
                        }
                        orph_nodes.append(mnode)
                        relations.append(new_rel)
                
                #Add to stack
                definitions += definition
                appendices += appendix
                related_words += relations
                categories += word_categories
                examples += w_examples
        if save_to_db:
            self.save_word_data(words, definitions, related_words, appendices, orph_nodes, categories, examples)

        return examples #fetched_data #related_words
    

    def save_word_data(self, words=[], definition=[], related_words=[], appendices=[], orph_nodes=[], categories=[], examples=[], insert=True, update=True):
        #Inserting to database
        cur = self.conn.cursor()
        if update:
            cur.executemany(f"UPDATE `{self.word_table}` SET query=%(query)s, word=%(word)s, etymology=%(etymology)s, language=%(language)s, wikiUrl=%(wikiUrl)s, isDerived=0 WHERE id=%(id)s", words)
            cur.executemany(f"UPDATE `{self.word_table}` SET query=%(query)s, word=%(word)s, etymology=%(etymology)s, language=%(language)s, wikiUrl=%(wikiUrl)s, isDerived=1 WHERE id=%(id)s", orph_nodes)
            self.conn.commit()
        if insert:
            cur.executemany(f"INSERT IGNORE INTO `{self.word_table}` (id, query, word, etymology, language, wikiUrl, isDerived) VALUES (%(id)s, %(query)s, %(word)s, %(etymology)s, %(language)s, %(wikiUrl)s, 0)", words)
            cur.executemany(f"INSERT IGNORE INTO `{self.word_table}` (id, query, word, etymology, language, wikiUrl, isDerived) VALUES (%(id)s, NULL, %(word)s, %(etymology)s, %(language)s, %(wikiUrl)s, 1)", orph_nodes)
            cur.executemany(f"INSERT IGNORE INTO {self.definitions_table} (id, wordId, partOfSpeech, text, headword) VALUES (%(definitionId)s, %(wordId)s, %(partOfSpeech)s, %(text)s, %(headword)s);", definition)
            cur.executemany(f"INSERT INTO `examples` (definitionId, quotation, transliteration, translation, source, example_text) VALUES (%(definitionId)s, %(quotation)s, %(transliteration)s, %(translation)s, %(source)s, %(example_text)s);", examples)
            if len(appendices) > 0:
                apx_q = f"INSERT IGNORE INTO {self.definitions_table}_apx (definitionId, appendixId) VALUES (%(definitionId)s, %(appendixId)s);"
                cur.executemany(apx_q, appendices)
            
            cur.executemany(f"INSERT IGNORE INTO {self.edge_table} (headDefinitionId, wordId, relationshipType) VALUES (%(def_hash)s, %(wordId)s, %(relationshipType)s)", related_words)
            cur.executemany(f"INSERT IGNORE INTO `word_categories` (wordId, categoryId) VALUES (%(wordId)s, %(categoryId)s)", categories)
            self.conn.commit()


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
                        "id": self.__apply_hash(a.get_text()),
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
        cur = self.conn.cursor()
        cur.executemany("INSERT IGNORE INTO `categories` (`id`, `title`, `text`, `sourceList`, `wikiUrl`) VALUES (%(id)s, %(title)s, %(text)s, %(sourceList)s, %(wikiUrl)s)", data)
        self.conn.commit()
        return data

    


# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
