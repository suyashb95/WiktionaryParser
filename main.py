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

EXPERIMENTAL = not False
deorphanization_level = 2
limit = 10 if EXPERIMENTAL else -1
vocab_file = 'json/collected.txt'

datasets = None
if EXPERIMENTAL:
    reset_db()
    datasets = upload_data('D:\Datasets', limit=limit)



tokenized_texts = convert_to_tokens(datasets)

# with open('json/tokenized_texts.json', 'w', encoding="utf8") as f:
#     f.write(json.dumps(tokenized_texts, indent=4, ensure_ascii=False))

global_tokens = get_global_token_counts(tokenized_texts)
for i in range(len(global_tokens)):
    global_tokens[i]['lang'] = dataset_langs.get(global_tokens[i]['dataset_name'])

with open('json/global_tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))

if EXPERIMENTAL:
    vocab = [(tok['token'], tok.get('lang')) for tok in global_tokens]
    existing_vocab_ids = [v['id'] for v in builder.get_vocab()]
    with open('json/vocab.json', 'w', encoding="utf8") as f:
        f.write(json.dumps(vocab, indent=4, ensure_ascii=False))
else:
    with open('json/vocab.json', 'r', encoding="utf8") as f:
        vocab = json.load(f)
    if os.path.isfile(vocab_file):
        with open(vocab_file, 'r', encoding="utf8") as f:
            existing_vocab_ids = [w.strip() for w in f.read().split('\n')]
    else:
        existing_vocab_ids = [v['id'] for v in builder.get_vocab()]

result = {}
vocab = sorted(dict(vocab).items())
vocab = tqdm.tqdm(vocab)
# if os.path.isfile(vocab_file):
    # os.remove(vocab_file)
    
print(existing_vocab_ids[:3])
for word, lang in vocab:
    vocab.set_description(f"[Started at {datetime.now().strftime('%H:%M:%S')}]")
    word = get_word_info_prep(word.strip())
    word_id = collector.apply_hash(word)
    if word_id in existing_vocab_ids:
        continue

    if len(word) <= 1:
        continue


    result = collect_info(word, lang, wait_time=.1, save_to_db=False)

    vocab.set_postfix_str(f'Last word: {fix_ar_display(word)} - Last URL: {parser.current_url}, - Fetched languages: {lang},')

    with open(vocab_file, 'a+', encoding="utf8") as f:
        f.write(word_id+'\n')

    if (vocab.n + 1) % 1000 == 0:
        collector.flush()

# collector.flush()

# for lv in range(deorphanization_level):
#     orphan_lex = builder.get_orphan_nodes()
#     for w in orphan_lex:
#         if w.get('language') is None:
#             w['language'] = "english"
#         else:
#             w['language'] = convert_language(w['language'], format="long")
#     if EXPERIMENTAL or True:
#         text_words = sorted({(w['word'], w['id'], w.get('language')) for w in orphan_lex})
#     print(f"Deorphanization (Level {lv+1:2d})")
#     text_words = tqdm.tqdm(text_words)
#     for word, id, lang in text_words:
#         text_words.set_description_str(f'Deorphanizing "{fix_ar_display(word)}" ({lang})')
#         result = deorphanize(word, id, lang)

#     # collector.save_word_data(**result)

# # export_graph_to_html('graph.html')