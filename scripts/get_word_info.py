import re
import time
import tqdm

from src.utils import convert_language
from .utils import *
import json


results = {}

def main(word, lang, wait_time=0, save_to_db=True, existing_vocab=[]):
    
    no_spaces_word = re.sub('\s', '_', word)
    if word != no_spaces_word: #If word has space, e.q to saying word is an entity
        fetched_data = {word: parser.fetch(no_spaces_word, query=word, language=lang)}
    else:
        if type(word) != str:
            prepped_word = ' '.join(word) #[0]
        else:
            prepped_word = word
        # print(f"Fetching all potentials for {prepped_word} ({lang})")
        fetched_data = parser.fetch_all_potential(prepped_word, query=word, language=lang)
    for k in fetched_data:
        element = fetched_data[k]
        e = collector.save_word(element, save_to_db=save_to_db)
        for k in e:
            results[k] = results.get(k, []) + e.get(k, [])
    if wait_time > 0:
        time.sleep(wait_time)

    #In-place deorphanization
    deorph_pbar = tqdm.tqdm(total=len(results['orph_nodes']), leave=False, position=1)
    orph_nodes = []
    while len(results['orph_nodes']) > 0:
        orph  = results['orph_nodes'].pop(0)
        if orph.get('wikiUrl') is None or orph.get('word') in existing_vocab:
            orph_nodes.append(orph)
            continue

        if orph.get('language') is None:
            orph['language'] = "english"
        else:
            orph['language'] = convert_language(orph['language'])

        sibling_word_data = parser.deorphanize(**orph)
        deorph_pbar.set_description_str(f"Deorphanizing '{fix_ar_display(orph.get('word'))}' ({len(collector.batch):2>d} in stack)")
        deorph_pbar.set_postfix(orph)
        deorph_pbar.refresh()

        e = collector.save_word(sibling_word_data, save_to_db=save_to_db, save_orphan=False, save_mentions=False)
        for k in e:
            results[k] = results.get(k, []) + e.get(k, [])

        deorph_pbar.update(1)
        if len(sibling_word_data) > 0:
            with open("resrdeorph.json", 'w', encoding="utf8") as f:
                json.dump(e, f, indent=2, sort_keys=True, ensure_ascii=False)

    results['orph_nodes'] = orph_nodes
    # if len(collector.batch) > 100:
    #     collector.flush()
    return results


# text_words = [
#     ('خيط', 'moroccan arabic'),
#     ('example', 'english'),
#     ('سماء', 'arabic'),
#     ('الدار البيضاء', 'arabic'),
#     ('البيت الأبيض', 'arabic'),
# ]

# results = main(text_words)

# with open('wordOut.json', 'w', encoding="utf8") as f:
#     f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
