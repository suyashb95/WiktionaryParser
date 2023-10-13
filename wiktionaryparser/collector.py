import csv
import os
import tqdm
import copy
from nltk.stem import *
import pymysql

from wiktionaryparser.core import WiktionaryParser 

class Collector:
    def __init__(self, host, username, password, db, word_table="words", dataset_table="data", edge_table="relationships"):
        self.host = host
        self.username = username
        self.password = password
        self.db = db

        self.word_table = word_table
        self.dataset_table = dataset_table
        self.edge_table = edge_table

        self.conn = pymysql.connect( 
            host=self.host, 
            user=self.username,  
            password = self.password, 
            db=self.db, 
        )

        self.__create_tables()

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
        ]
        for query in queries:
            # print(query)
            cur.execute(query)

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
        for table in [self.dataset_table, self.word_table]:
            cur.execute(f"TRUNCATE TABLE {table}")
            cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
        # cur.execute(f"TRUNCATE TABLE {self.edge_table}")
        # cur.execute(f"TRUNCATE TABLE {self.word_table}")
    
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
                print('\n\n'+query+'\n\n')
                raise(err)
                break    
        self.conn.commit()

    def insert_dataset(self, path):
        dataset_name = path.split('/')[-1].replace('.csv', '')
        file_rows = self.coll.adapt_csv_dataset(path, dataset_name=dataset_name)
        self.coll.insert_data(file_rows, dataset_name=dataset_name, task="Sentiment Analysis")


    def save_word(self, fetched_data):
        cur = self.conn.cursor()
        for e in fetched_data:
            word = {
                k: e.get(k) for k in ['etymology', 'language', "query", 'word']
            }
            cur.execute(f"INSERT INTO `{self.word_table}` (query, word, etymology, language) VALUES (%(query)s, %(word)s, %(etymology)s, %(language)s)", word)
            word_id = cur.lastrowid
            print(word_id)


            break
        self.conn.commit()
        return (e.get("definitions"))



# preprocessor = Preprocessor(stemmer=ARLSTem(), normalizer=Normalizer(waw_norm="و"))
