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
from scripts.word_magnitude import influential_words
from src.utils import convert_language, flatten_dict

EXPERIMENTAL = not False
PHASE = 1
deorphanization_level = 2
limit = 3 if EXPERIMENTAL else -1
vocab_file = 'json/collected.txt'
top_k = 3 if EXPERIMENTAL else 0

if not os.path.isdir('./json'):
    os.mkdir('json')

datasets = None
if PHASE <= 1:
    reset_db()
    datasets = upload_data('D:\Datasets', limit=limit)

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
    if EXPERIMENTAL:
        with open('json/global_tokens.json', 'r', encoding="utf8") as f:
            global_tokens = json.load(f)
        existing_vocab_ = [v[vocab_id_key] for v in builder.get_vocab()]
        vocab = [tok for tok in global_tokens if tok.get('token') not in existing_vocab_]
        with open('json/vocab.json', 'w', encoding="utf8") as f:
            f.write(json.dumps(vocab, indent=4, ensure_ascii=False))
    else:
        with open('json/vocab.json', 'r', encoding="utf8") as f:
            vocab = json.load(f)

        existing_vocab_ = builder.get_vocab(category_info=False)
        print(json.dumps(existing_vocab_[:2], indent=4))
        existing_vocab_ = sorted({v[vocab_id_key] for v in existing_vocab_})        

    result = {}
    vocab = [w for w in vocab if w['token'] not in existing_vocab_]
    # vocab = vocab[:3]
    vocab = tqdm.tqdm(vocab, position=0)
    if os.path.isfile(vocab_file):
        os.remove(vocab_file)

    collector.auto_flush_after = -1
    for e in vocab:
        word = e['token']
        if len(word) <= 1:
            continue


        lang = e.get('lang')
        vocab.set_description(f"[Started at {datetime.now().strftime('%H:%M:%S')}] - ({fix_ar_display(word)})")
        word = get_word_info_prep(word.strip())
        word_id = collector.apply_hash(word)
        
        result_ = collect_info(word, lang, wait_time=.1, save_to_db=True)
        for k in result_:
            result[k] = result.get(k, []) + result_[k]
        with open("resres.json", 'w', encoding="utf8") as f:
            json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        
        vocab.set_postfix({k: len(result[k]) for k in result})
        with open(vocab_file, 'a+', encoding="utf8") as f:
            f.write(word+'\n')
        
        if len(result.get('definitions', [])) >= 10000:
            collector.update_word_data(**result)
            collector.insert_word_data(**result)
            result = {}
            # 1/0

    collector.flush()

if PHASE <= 4 and not EXPERIMENTAL:
    collector.auto_flush_after = 10
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
            result = deorphanize(word, id, lang, save_to_db=True)

    collector.flush()

if PHASE <= 5 and not EXPERIMENTAL:
    collector.export_to_csv('./backup/csv_export/')
# # export_graph_to_html('graph.html')