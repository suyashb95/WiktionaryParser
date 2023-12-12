import sys
from nltk import stem
import pymysql
sys.path.append('.')
from bidi.algorithm import get_display
import arabic_reshaper
from src.graph import GraphBuilder

from src.collector import Collector
from src.core import WiktionaryParser
from src.preprocessing import Normalizer, Preprocessor

parser = WiktionaryParser()
prep = Preprocessor()

conn = pymysql.connect(host="localhost", user="root", password="", db="knowledge_graph")
collector = Collector(conn)
builder = GraphBuilder(conn)

deorphanize_prep = Preprocessor(unshakl=True)
get_word_info_prep = Preprocessor(stemmer=stem.ARLSTem(), return_type="str")
dataset_2_tokens_prep = Preprocessor(normalizer=Normalizer('أ', alef_norm='ا'))
#Prep above is too aggressive, please fix

reset_db = lambda : collector.erase_db()
fix_ar_display = lambda text: get_display(arabic_reshaper.reshape(text))