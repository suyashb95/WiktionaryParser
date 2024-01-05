from datetime import datetime
import json
import os
import re

import tqdm

from scripts.utils import fix_ar_display, reset_db, parser, builder, get_word_info_prep
from scripts.utils import collector
from scripts.dataset_uploading import main as upload_data
from scripts.dataset_uploading import dataset_langs
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
from scripts.visualize_interactive_graph import export_graph_to_html
from src.utils import convert_language

<<<<<<< HEAD
EXPERIMENTAL = False
PHASE = 1
=======
EXPERIMENTAL = not False
PHASE = 4
>>>>>>> b8b12f96f59c4523f9bacb1d22245cfe4f3d0f78
deorphanization_level = 2
limit = 3 if EXPERIMENTAL else -1
vocab_file = 'json/collected.txt'

if not os.path.isdir('./json'):
    os.mkdir('json')

datasets = None
if PHASE <= 1:
    reset_db()
<<<<<<< HEAD
    try:
        datasets = upload_data('D:\Datasets', limit=limit)
    except StopIteration:
        datasets = upload_data('E:\Banouz\Datasets', limit=limit)
=======
    datasets = upload_data('D:\Datasets', limit=limit)
    if os.path.isfile(vocab_file):
        os.remove(vocab_file)
>>>>>>> b8b12f96f59c4523f9bacb1d22245cfe4f3d0f78

if PHASE <= 2:
    tokenized_texts = convert_to_tokens(datasets)

    global_tokens = get_global_token_counts(tokenized_texts)
    for i in range(len(global_tokens)):
        global_tokens[i]['lang'] = dataset_langs.get(global_tokens[i]['dataset_name'])

    with open('json/global_tokens.json', 'w', encoding="utf8") as f:
        f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))

if PHASE <= 3:
    vocab_id_key = 'word'
    #Setting existing vocab
    if os.path.isfile('json/vocab.json'):
        with open('json/vocab.json', 'r', encoding="utf8") as f:
            vocab = json.load(f)

        existing_vocab_ = builder.get_vocab(category_info=False)
        existing_vocab_ = sorted({v[vocab_id_key] for v in existing_vocab_})        
    else:
        with open('json/global_tokens.json', 'r', encoding="utf8") as f:
            global_tokens = json.load(f)
        existing_vocab_ = [v[vocab_id_key] for v in builder.get_vocab()]
        vocab = [tok for tok in global_tokens if tok.get('token') not in existing_vocab_]
        with open('json/vocab.json', 'w', encoding="utf8") as f:
            f.write(json.dumps(vocab, indent=4, ensure_ascii=False))
    #Adding tokens from collected vocab file
    if os.path.isfile(vocab_file):
        with open(vocab_file, 'r', encoding="utf8") as f:
            existing_vocab_ += [w.strip() for w in f.readlines()]


    result = {}
    vocab = [w for w in vocab if w['token'] not in existing_vocab_]
    # vocab = vocab[:15]
    vocab = tqdm.tqdm(vocab, position=0)


    collector.auto_flush_after = 100
    print(f"\n=========== Phase 3 begins at {datetime.now().strftime('%H:%M:%S')} ===========")
    for e in vocab:
        word = e['token']
        if len(word) <= 1 or word in existing_vocab_:
            continue

        lang = e.get('lang')
        vocab.set_description(f"[Started at {datetime.now().strftime('%H:%M:%S')}] - ({fix_ar_display(word)})")
        word = get_word_info_prep(word.strip())

        
        result = collect_info(word, lang, wait_time=.1, save_to_db=True, existing_vocab=existing_vocab_)

        # with open("json/resres.json", 'w', encoding="utf8") as f:
        #     json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        
        derived_words = sorted({w['word'] for w in result.get('words', [])})
        derived_words.insert(0, word)

        result = {k: len(result[k]) for k in result}
        vocab.set_postfix(result)
        existing_vocab_.append(e['token'])

        with open(vocab_file, 'a+', encoding="utf8") as f:
            f.writelines([w+'\n' for w in derived_words])


    collector.flush()

if PHASE <= 4:
    orphan_urls = sorted({(w.get('wikiUrl'), w.get('word'), w.get('query')) for w in builder.get_orphan_nodes()})
    orphan_lex = []
    for url, w, q in orphan_urls:
        lang = re.search('#(\w+)$', url)
        if lang is not None:
            lang = lang.group(1)

        orphan_lex.append({
            'wikiUrl': url, 
            'language': lang,
            'word': w,
            'query': q
        })
    
    # orphan_lex = orphan_lex[:10]
    orphan_lex = tqdm.tqdm(orphan_lex)

    #Ready to deorphanize
    deorphed_words = []
    collector.auto_flush_after = 25
    for orph in orphan_lex:
        orphan_lex.set_postfix(orph)
        result = parser.deorphanize(**orph)
        collector.save_word(result, save_to_db=True, save_orphan=False, save_mentions=False)

    collector.flush()


# if PHASE <= 4 and not EXPERIMENTAL:
#     collector.auto_flush_after = 10
#     for lv in range(deorphanization_level):
#         orphan_lex = builder.get_orphan_nodes()
#         for w in orphan_lex:
#             if w.get('language') is None:
#                 w['language'] = "english"
#             else:
#                 w['language'] = convert_language(w['language'], format="long")
#         if True:
#             text_words = dict((w['id'], w) for w in orphan_lex).items()
#             text_words = sorted(text_words, key=lambda x: x[0])
#         print(f"Deorphanization (Level {lv+1:2d})")
#         text_words = tqdm.tqdm(text_words)
#         for id, e in text_words:
#             lang = e.get('language')
#             word = e['word']
#             text_words.set_description_str(f'Deorphanizing "{fix_ar_display(word)}" ({lang}) - ({len(collector.batch):02d} in stack)')
#             result = deorphanize(word, id, lang, save_to_db=True)

#     collector.flush()

if PHASE <= 5 and not EXPERIMENTAL:
    collector.export_to_csv('./backup/csv_export/')
# # export_graph_to_html('graph.html')
