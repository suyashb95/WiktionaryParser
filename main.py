import json

import tqdm

from scripts.utils import fix_ar_display, reset_db, collector, builder
from scripts.dataset_uploading import main as upload_data
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
from scripts.deorphanize import main as deorphanize
from scripts.visualize_interactive_graph import export_graph_to_html
from src.utils import convert_language

EXPERIMENTAL = not False
deorphanization_level = 2
limit = 1000 if EXPERIMENTAL else -1

datasets = None
# if EXPERIMENTAL:
#     reset_db()
#     datasets = upload_data('D:\Datasets', limit=limit)



tokenized_texts = convert_to_tokens(datasets)

with open('json/tokenized_texts.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(tokenized_texts, indent=4, ensure_ascii=False))

global_tokens = get_global_token_counts(tokenized_texts)

with open('json/global_tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))

if EXPERIMENTAL:
    vocab = [(tok['token'], tok.get('lang', 'arabic')) for tok in global_tokens]

    with open('json/vocab.json', 'w', encoding="utf8") as f:
        f.write(json.dumps(vocab, indent=4, ensure_ascii=False))
else:
    with open('json/vocab.json', 'r', encoding="utf8") as f:
        vocab = json.load(f)

    existing_vocab_words = [v[k] for v in builder.get_vocab() for k in ['word', 'query']]
    vocab = [(w, l) for w, l in vocab if w not in existing_vocab_words]

result = {}
vocab = tqdm.tqdm(vocab)
for word, lang in vocab:
    word = word.strip()
    vocab.set_description_str(f'Collecting info for "{fix_ar_display(word)}" ({lang})')
    if len(word) < 1:
        continue
    result = collect_info(word, lang, wait_time=.1)
    with open('json/collected.txt', 'a+', encoding="utf8") as f:
        f.write(word+'\n')
    # if EXPERIMENTAL:
    #     if (vocab.n) % 500 == 0:
    #         collector.save_word_data(**result)

    # # elif (vocab.n) % 1000 == 0:
    # #     collector.flush()


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