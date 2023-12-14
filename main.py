from datetime import datetime
import json
import os

import tqdm

from scripts.utils import fix_ar_display, reset_db, parser, builder, get_word_info_prep
from scripts.utils import collector
from scripts.dataset_uploading import main as upload_data
from scripts.dataset_uploading import dataset_langs
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
from scripts.deorphanize import main as deorphanize
from scripts.visualize_interactive_graph import export_graph_to_html
from src.utils import convert_language

EXPERIMENTAL = False
deorphanization_level = 2
limit = 100 if EXPERIMENTAL else -1
vocab_file = 'json/collected.txt'

datasets = None
# if EXPERIMENTAL:
#     reset_db()
#     datasets = upload_data('D:\Datasets', limit=limit)



tokenized_texts = convert_to_tokens(datasets)

global_tokens = get_global_token_counts(tokenized_texts)
for i in range(len(global_tokens)):
    global_tokens[i]['lang'] = dataset_langs.get(global_tokens[i]['dataset_name'])

with open('json/global_tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))

vocab_id_key = 'word'
if EXPERIMENTAL:
    existing_vocab_ = [v[vocab_id_key] for v in builder.get_vocab()]
    vocab = [tok for tok in global_tokens if tok.get('token') not in existing_vocab_]
    with open('json/vocab.json', 'w', encoding="utf8") as f:
        f.write(json.dumps(vocab, indent=4, ensure_ascii=False))
else:
    with open('json/vocab.json', 'r', encoding="utf8") as f:
        vocab = json.load(f)
    if os.path.isfile(vocab_file) and False:
        with open(vocab_file, 'r', encoding="utf8") as f:
            existing_vocab_ = [w.strip() for w in f.read().split('\n')]
    else:
        existing_vocab_ = builder.get_vocab(category_info=False)
        print(json.dumps(existing_vocab_[:2], indent=4))
        existing_vocab_ = sorted({v[vocab_id_key] for v in existing_vocab_})        

result = {}
# vocab = sorted(dict(vocab).items())
# collector.auto_flush_after = len(vocab) // 10 #Flush 10 times throughout the processing loop
collector.auto_flush_after = 500
# print(vocab[:1])
# print(existing_vocab_[:1])
# 1/0
vocab = [w for w in vocab if w['token'] not in existing_vocab_]
vocab = tqdm.tqdm(vocab, position=0)
# if os.path.isfile(vocab_file):
    # os.remove(vocab_file)

for e in vocab:
    word = e['token']
    if len(word) <= 1:
        continue
    # if word in existing_vocab_:
    #     continue
    lang = e.get('lang')
    vocab.set_description(f"[Started at {datetime.now().strftime('%H:%M:%S')}] - ({len(collector.batch):02d} in stack)")
    word = get_word_info_prep(word.strip())
    word_id = collector.apply_hash(word)
    vocab.set_postfix_str(f'Word: {fix_ar_display(word)} - Fetched languages: {lang},')
    
    result = collect_info(word, lang, wait_time=.1, save_to_db=False)


    with open(vocab_file, 'a+', encoding="utf8") as f:
        f.write(word_id+'\n')

collector.flush()

for lv in range(deorphanization_level):
    orphan_lex = builder.get_orphan_nodes()
    for w in orphan_lex:
        if w.get('language') is None:
            w['language'] = "english"
        else:
            w['language'] = convert_language(w['language'], format="long")
    if EXPERIMENTAL or True:
        text_words = dict((w['id'], w) for w in orphan_lex).items()
        text_words = sorted(text_words, key=lambda x: x[0])
    print(f"Deorphanization (Level {lv+1:2d})")
    text_words = tqdm.tqdm(text_words)
    for id, e in text_words:
        lang = e.get('language')
        word = e['word']
        text_words.set_description_str(f'Deorphanizing "{fix_ar_display(word)}" ({lang}) - ({len(collector.batch):02d} in stack)')
        result = deorphanize(word, id, lang, save_to_db=False)

collector.flush()


collector.export_to_csv('./backup/csv_export/')
# # export_graph_to_html('graph.html')