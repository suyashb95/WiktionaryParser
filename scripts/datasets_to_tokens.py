import random
random.seed(222)
from collections import Counter
from .utils import *

def convert_to_tokens(dataset_name=None, sample_size = 0):
    results = builder.get_dataset(dataset_name=dataset_name)

    k = "dataset_name"  # The key for stratification

    k_counts = set(entry[k] for entry in results)
    

    stratified_samples = []
    for unique_k in k_counts:
        entries_with_k = [entry for entry in results if entry.get(k) == unique_k]
        if sample_size > 1:
            if len(entries_with_k) >= sample_size:
                entries_with_k = random.sample(entries_with_k, sample_size)
                # entries_with_k = entries_with_k[:sample_size]


        for entry in entries_with_k:
            raw_text = entry.get('text')
            prepped_text = dataset_2_tokens_prep(raw_text)
            raw_text = dataset_2_tokens_prep.tokenize(raw_text)
            prepped_text_tokens = [(tok, raw) for tok, raw in zip(prepped_text, raw_text) if len(tok.strip()) > 0]
            
            prepped_text = ' '.join(prepped_text)
            prepped_text = dataset_2_tokens_prep.strip_spaces(prepped_text)            
            entry['prepped_text'] = prepped_text

            entry['tokens'] = Counter(prepped_text_tokens)
            entry['tokens'] = [{
                "token": tok,
                "unprocessed_token": raw,
                "count": count,
            } for (tok, raw), count in entry['tokens'].items()]
            stratified_samples.append(entry)

    return stratified_samples

def get_global_token_counts(tokenized_texts):
    global_tokens = {}
    for i in range(len(tokenized_texts)):
        tokens = tokenized_texts[i]['tokens']
        dataset_name = tokenized_texts[i]['dataset_name']
        tokens = {(tok['token'], dataset_name): tok['count'] for tok in tokens}
        for tok in tokens:
            global_tokens[tok] = global_tokens.get(tok, 0) + tokens[tok]

    global_tokens = [{
        "token": tok,
        "dataset_name": dataset_name,
        "frequency": n
    } for (tok, dataset_name), n in global_tokens.items()]
    global_tokens = sorted(global_tokens, key=lambda x: x.get("frequency", 0), reverse=True)
    return global_tokens

# stratified_samples = main()
# with open('dsInfo.json', 'w', encoding="utf8") as f:
#     f.write(json.dumps(stratified_samples, indent=4, ensure_ascii=False))
