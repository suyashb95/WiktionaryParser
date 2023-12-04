import json
from scripts.utils import reset_db
from scripts.dataset_uploading import main as upload_data
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
from scripts.deorphanize import main as deorphanize

EXPERIMENTAL = True
reset_db()
limit = 5 if EXPERIMENTAL else -1
datasets = upload_data('D:\Datasets', limit=limit)
tokenized_texts = convert_to_tokens(datasets)
global_tokens = get_global_token_counts(tokenized_texts)

if EXPERIMENTAL:
    global_tokens = global_tokens[:10]


vocab = [(tok['token'], tok.get('lang', 'arabic')) for tok in global_tokens]
vocab = collect_info(vocab, wait_time=.1)
deorphanize(wait_time=.1)

with open('tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(vocab, indent=4, ensure_ascii=False))