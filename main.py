import json
from scripts.utils import reset_db
from scripts.dataset_uploading import main as upload_data
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
from scripts.deorphanize import main as deorphanize
from scripts.visualize_interactive_graph import export_graph_to_html

EXPERIMENTAL = 0
deorphanization_level = 2

# reset_db()
limit = 5 if EXPERIMENTAL else -1
# datasets = upload_data('D:\Datasets', limit=limit)
datasets = None
tokenized_texts = convert_to_tokens(datasets)
global_tokens = get_global_token_counts(tokenized_texts)

if EXPERIMENTAL:
    global_tokens = global_tokens[:10]

with open('json/global_tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))

vocab = [(tok['token'], tok.get('lang', 'arabic')) for tok in global_tokens]

with open('json/vocab.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(vocab, indent=4, ensure_ascii=False))

vocab = collect_info(vocab, wait_time=.1)
for lv in range(deorphanization_level):
    print(f"Deorphanization (Level {lv+1:2d})")
    deorphanize(wait_time=.1)


export_graph_to_html('graph.html')