import json
import pymysql
from src.collector import Collector

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
coll = Collector(conn)

# category_links = coll.__get_category_data()

# with open('category_links.json', 'w', encoding="utf8") as f:
#     f.write(json.dumps(category_links, indent=4, ensure_ascii=False))

# (coll.export_to_csv('./backup/csv_export/'))
