from datetime import datetime
import json
import os
import re

import tqdm

from scripts.utils import fix_ar_display, reset_db, parser, builder, get_word_info_prep
from scripts.utils import collector, inspector
from scripts.dataset_uploading import main as upload_data
from scripts.dataset_uploading import dataset_langs
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import collect_info
from scripts.visualize_interactive_graph import export_graph_to_html
from scripts.word_magnitude import influential_words
from src.utils import convert_language, export_to_json, flatten_dict

os.system("cls")
EXPERIMENTAL = False
PHASE = 1
deorphanization_level = 2
limit = 3 if EXPERIMENTAL else 10
vocab_file = 'json/collected.txt'
top_k = 3 if EXPERIMENTAL else 0

if not os.path.isdir('./json'):
    os.mkdir('json')


datasets = None
if PHASE <= 1:
    reset_db()
    try:
        datasets = upload_data('D:\Datasets', limit=limit)
    except StopIteration:
        datasets = upload_data('E:\Banouz\Datasets', limit=limit)

if PHASE <= 2:
    tokenized_texts = convert_to_tokens(datasets)

    tokenized_texts = convert_to_tokens(None)
    starting_vocab_ = influential_words(tokenized_texts, top_k=top_k)
    starting_vocab_ = [{"dataset_name": dn, "token": sorted(tok.keys())} for (dn, _), tok in starting_vocab_.items()]
    global_tokens = []
    
    for e in starting_vocab_:
        global_tokens += flatten_dict(e)

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
    if os.path.isfile(vocab_file):
        os.remove(vocab_file)
    
    # if EXPERIMENTAL:        
    #     vocab = [
    #         {"token": "كبير", "lang": ['arabic']},
    #         {"token": "مصر", "lang": ['arabic']},
    #     ]

    print(f"\n=========== Phase 3 begins at {datetime.now().strftime('%H:%M:%S')} ===========")
    vocab = tqdm.tqdm(vocab, position=0)
    collector.auto_flush_after = 100
    for e in vocab:
        word = e['token']
        if len(word) <= 1 or word in existing_vocab_:
            continue

        lang = e.get('lang')
        # lang = ['arabic']
        vocab.set_description(f"[Started at {datetime.now().strftime('%H:%M:%S')}] - ({fix_ar_display(word)})")
        word = get_word_info_prep(word.strip())

        result = collect_info(word, lang, wait_time=.1, save_to_db=True, existing_vocab=existing_vocab_)
        
        result_len = {k: len(result[k]) for k in result}
        vocab.set_postfix(result_len)
        existing_vocab_.append(e['token'])

        # export_to_json(result, "results.json")
        collector.insert_word_data(**result)
        collector.update_word_data(**result)

if PHASE <= 4:
    SUPPORTED_LANGS = {'arabic', 'english'}
    for rd, default_lang in enumerate(['english', None], start=1):
        orphan_urls = sorted({(w.get('wikiUrl'), w.get('word'), w.get('query')) for w in builder.get_orphan_nodes()})
        orphan_lex = []
        for url, w, q in orphan_urls:
            lang = re.search('#(\w+)$', url)
            if lang is not None:
                lang = lang.group(1)
                if not any([l in lang.lower() for l in SUPPORTED_LANGS]):
                    lang = default_lang
            else:
                lang = default_lang

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
            collector.save_word(result, save_to_db=True, 
                                save_orphan=False, # (rd == deorphanization_level), 
                                save_mentions=False
                            )

    # collector.flush()



# if PHASE <= 5 and not EXPERIMENTAL:
#     collector.export_to_csv('./backup/csv_export/')


if PHASE <= 6:
    export_graph_to_html('graph.html')
