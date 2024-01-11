from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def influential_words(tokenized_texts, top_k=5, score_metric="tfidf", task = None):
    dataset_names = {}
    if task is not None:
        data = [obj for obj in tokenized_texts if obj.get('task') == task]
    else:
        data = tokenized_texts.copy()

    for name in sorted({obj.get('dataset_name') for obj in data}):
        dataset_names[name] = sorted({obj.get('label') for obj in data if obj.get('dataset_name') == name})

    word_magnitudes = {}
    for name in dataset_names:
        texts = [obj.get('text', '') for obj in data if obj.get('dataset_name') == name]
        vectorizer = TfidfVectorizer().fit(texts)
        vocab = zip(vectorizer.vocabulary_, vectorizer.idf_)
        for label in dataset_names[name]:
            label_texts = [obj.get('text', '') for obj in data if obj.get('dataset_name') == name and obj.get('label') == label]
            vectorizer = TfidfVectorizer(use_idf=False).fit(label_texts)
            label_tfidfs = vectorizer.transform(label_texts).toarray()
            label_avg_tfidfs = np.mean(label_tfidfs, axis=0)
            for (word, idf), freq in zip(vocab, label_avg_tfidfs):
                d = {
                    "word": word,
                    "freq": freq,
                    "idf": idf,
                    "tfidf": freq*idf,
                    "label": label,
                    "dataset_name": name
                }
                if (name, label) not in word_magnitudes:
                    word_magnitudes[(name, label)] = []
                word_magnitudes[(name, label)].append(d)

    word_magnitudes = {k: sorted(v, key=lambda x: x.get(score_metric))[-top_k:] for k, v in word_magnitudes.items()}
    word_magnitudes = {k: {e['word']: e[score_metric] for e in v} for k, v in word_magnitudes.items()}
    return word_magnitudes 

# grouped_data = group_and_list_tokens(tokenized_texts)
# token_frequencies = calculate_token_frequencies(grouped_data)
