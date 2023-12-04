import re
import tqdm
from .utils import *
import json


def main(text_words):
    results = []
    text_words = tqdm.tqdm(text_words)
    for word, lang in text_words:
        no_spaces_word = re.sub('\s', '_', word)
        if word != no_spaces_word: #If word has space, e.q to saying word is an entity
            fetched_data = {word: parser.fetch(no_spaces_word, language=lang)}
        else:
            prepped_word = ' '.join(get_word_info_prep(word)) #[0]
            # print(f"Fetching all potentials for {prepped_word} ({lang})")
            fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
        for k in fetched_data:
            element = fetched_data[k]
            results += collector.save_word(element, save_to_db=True)

    return results


text_words = [
    ('خيط', 'moroccan arabic'),
    ('example', 'english'),
    ('سماء', 'arabic'),
    ('الدار البيضاء', 'arabic'),
    ('البيت الأبيض', 'arabic'),
]

results = main(text_words)

with open('wordOut.json', 'w', encoding="utf8") as f:
    f.write(json.dumps(results, indent=4, ensure_ascii=False))

    
