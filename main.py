import json
from scripts.utils import reset_db
from scripts.dataset_uploading import main as upload_data
from scripts.datasets_to_tokens import convert_to_tokens, get_global_token_counts
from scripts.get_word_info import main as collect_info
# from scripts.deorphanize import main as deorphanize

EXPERIMENTAL = True
reset_db()
datasets = upload_data('D:\Datasets')
tokenized_texts = convert_to_tokens(datasets)
print(tokenized_texts)
1/0
global_tokens = get_global_token_counts(tokenized_texts)

if EXPERIMENTAL:
    global_tokens = global_tokens[:2]


vocab = [(tok['token'], tok['lang']) for tok in global_tokens]
vocab = collect_info(vocab)

with open('tokens.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(global_tokens, indent=4, ensure_ascii=False))