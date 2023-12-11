import re
import time
import tqdm
from src.utils import convert_language
from .utils import *

results = {}
def main(word, i, lang, save_to_db=True):
    no_spaces_word = re.sub('\s', '_', word)
    if word != no_spaces_word: #If word has space, e.q to saying word is an entity
        fetched_data = {word: parser.fetch(no_spaces_word, language=lang)}
    else:
        prepped_word = ' '.join(deorphanize_prep(word)) #[0]
        fetched_data = parser.fetch_all_potential(prepped_word, language=lang)
    for k in fetched_data:
        element = fetched_data[k]

        #Add original id so that it matches during the update
        for i in range(len(element)):
            element[i].update({'id': i})
        e = collector.save_word(element, save_to_db=save_to_db, save_orphan=False)
        for k in e:
            results[k] = results.get(k, []) + e.get(k, [])
    return results
    

if __name__ == "__main__":
    text_words=None
    limit=-1
    wait_time=0
    if text_words is None:
        orphan_lex = builder.get_orphan_nodes()
        for w in orphan_lex:
            if w.get('language') is None:
                w['language'] = "english"
            else:
                w['language'] = convert_language(w['language'], format="long")

        text_words = sorted({(w['word'], w['id'], w.get('language')) for w in orphan_lex})
    # print(text_words)
    if limit > 1:
        text_words = text_words[:limit]
    text_words = tqdm.tqdm(text_words)
    for word, id, lang in text_words:
        text_words.set_description_str(f'Deorphanizing "{fix_ar_display(word)}" ({lang})')
        res = main(word, id, lang)
        if wait_time > 0:
            time.sleep(wait_time)


    # with open('orphOut.json', 'w', encoding="utf8") as f:
    #     f.write(json.dumps(results, indent=4, ensure_ascii=False))

    # print(len(builder.get_orphan_nodes()))
