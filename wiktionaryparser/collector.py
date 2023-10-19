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


class Collector:
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

        
        self.__create_tables()
        # with open('appendix.json', 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.__get_appendix_data(), indent=2, ensure_ascii=False))

    def __apply_hash(self, s):
        return hashlib.sha256(s.encode()).hexdigest()
    
    def __create_tables(self):
        cur = self.conn.cursor()
        queries = [f"""
                CREATE TABLE IF NOT EXISTS {self.dataset_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY, 
                    text VARCHAR(1023) NOT NULL, 
                    label VARCHAR(255) NOT NULL, 
                    dataset_name VARCHAR(255), 
                    task VARCHAR(255)
                ); 
            """, 
            f"CREATE TABLE IF NOT EXISTS {self.word_table} (id INT AUTO_INCREMENT PRIMARY KEY, word VARCHAR(255), query VARCHAR(255), language VARCHAR(255), etymology TEXT);",
            f"""
            CREATE TABLE IF NOT EXISTS {self.definitions_table} (
                    `id` VARCHAR(64), 
                    `wordId` INT NOT NULL , 
                    `partOfSpeech` VARCHAR(16) NOT NULL , 
                    `text` VARCHAR(1024) NOT NULL , 
                    `headword` VARCHAR(256) NOT NULL , 
                    PRIMARY KEY (`id`(64)),
                    CONSTRAINT fk_wordId FOREIGN KEY (wordId)  
                    REFERENCES {self.word_table}(id)  
                    ON DELETE CASCADE  
                    ON UPDATE CASCADE 
                );
            """,
            #CREATE APPENDIX TABLE HERE
            f"""
            CREATE TABLE IF NOT EXISTS appendix (
                    id VARCHAR(64), 
                    `label` VARCHAR(255) NOT NULL , 
                    `description` VARCHAR(1024) , 
                    `wikiUrl` VARCHAR(255) ,
                    `category` VARCHAR(255) ,
                    PRIMARY KEY (`id`(64))
                );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.definitions_table}_apx (
                    `definitionId` VARCHAR(64) NOT NULL , 
                    `appendixId` VARCHAR(64) NOT NULL , 
                    CONSTRAINT fk_definitionId FOREIGN KEY (definitionId)  
                    REFERENCES {self.definitions_table}(id)  
                    ON DELETE CASCADE  
                    ON UPDATE CASCADE , 
                    CONSTRAINT fk_definitionApx FOREIGN KEY (appendixId)  
                    REFERENCES appendix (id)  
                    ON DELETE CASCADE  
                    ON UPDATE CASCADE 
                );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.edge_table} (
                    `definitionId` VARCHAR(64) NOT NULL ,
                    `word` VARCHAR(64) , 
                    `relationshipType` VARCHAR(64) , 
                    CONSTRAINT fk_definitionIdRel FOREIGN KEY (definitionId)  
                    REFERENCES {self.definitions_table}(id)  
                    ON DELETE CASCADE  
                    ON UPDATE CASCADE 
                );
            """,
        ]
        for query in tqdm.tqdm(queries):
            cur.execute(query)
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
            self.definitions_table+"_apx", self.edge_table,
            self.definitions_table, self.dataset_table, self.word_table
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
        
    def save_word(self, fetched_data):
        hash_maxlen = 48
        cur = self.conn.cursor()
        related_words = []
        for row in fetched_data:
            print(row.keys())
            word = {
                k: row.get(k) for k in ['etymology', 'language', "query", 'word']
            }
            cur.execute(f"INSERT INTO `{self.word_table}` (query, word, etymology, language) VALUES (%(query)s, %(word)s, %(etymology)s, %(language)s)", word)
            self.conn.commit()
            word_id = cur.lastrowid
                        
            definitions = row.get("definitions", [])         

            for element in definitions:
                element_pos = element.get("partOfSpeech")
                for rw in element.get("relatedWords", []):
                    rw['wordId'] = word_id
                    rw['pos'] = element_pos

                    related_words += flatten_dict(rw)
                #Definitions
                definition = {
                    "wordId": word_id, #FOREIGN KEY
                    "partOfSpeech": element_pos,
                    "text": element.get("text", [])
                }
            
                #Add definitions
                definition = flatten_dict(definition)
                for i in range(len(definition)):
                    definition[i].update(definition[i].get("text", {}))
                    for k_ in ["examples", "categories"]:
                        if k_ in definition[i]:
                            definition[i].pop(k_)
                            
                    appendix = definition[i].pop('appendix_tags')
                    appendix = [a.lower().strip() for a in appendix]
                    appendix = [a.replace(u"\xa0", ' ') for a in appendix]

                    #Get a unique hash that encodes word, its POS and its explanation (to disambiguate verbal form from nominal form)
                    unique_w_hash = f"{definition[i].get('wordId')}_{definition[i].get('partOfSpeech')}_{definition[i].get('raw_text')[:hash_maxlen]}"
                    unique_w_hash = self.__apply_hash(unique_w_hash)
                    definition[i]['definitionId'] = unique_w_hash #PRIMARY KEY

                    #Isolate appendix for its own table
                    appendix = {
                        "appendixId": [
                            self.__apply_hash(e) for e in appendix
                        ] #FOREIGN KEY
                    }
                    cur.execute(f"INSERT INTO {self.definitions_table} (id, wordId, partOfSpeech, text, headword) VALUES (%(definitionId)s, %(wordId)s, %(partOfSpeech)s, %(text)s, %(headword)s);", definition[i])
                    self.conn.commit()
                    appendix['definitionId'] = unique_w_hash
                    appendix = flatten_dict(appendix)
                    if len(appendix) > 0:
                        apx_q = f"INSERT IGNORE INTO {self.definitions_table}_apx (definitionId, appendixId) VALUES (%(definitionId)s, %(appendixId)s);"
                        cur.executemany(apx_q, appendix)
                        self.conn.commit()

        for i in range(len(related_words)):
            related_words[i].update(related_words[i].get("words", {}))
            def_hash = f"{related_words[i].get('wordId')}_{related_words[i].get('pos')}_{related_words[i].get('def_text')[:hash_maxlen]}"
            def_hash = self.__apply_hash(def_hash)
            related_words[i]['def_hash'] = def_hash

            for k in ['pos', 'def_text']:
                if k in related_words[i]:
                    del related_words[i][k]
            # print("RW {} keys: {}".format(i, related_words[i].keys()))

        cur.executemany(f"INSERT INTO {self.edge_table} (definitionId, word, relationshipType) VALUES (%(def_hash)s, %(words)s, %(relationshipType)s)", related_words)
        self.conn.commit()
        return related_words #fetched_data #related_words


# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
