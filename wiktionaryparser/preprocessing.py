import re
from nltk.tokenize import word_tokenize
import string
from bidi.algorithm import get_display


class Normalizer:
    # Normalize the hamza, the waw, the alef-maqsura, taa-marbuta, indian numbers (configurable attrs)
    def __init__(self, hamza_norm=None, waw_norm=None, alef_norm=None, alef_maqsura_norm=None, taa_marbuta_norm=None, normalize_indian_digits=False):
        self.alef_norm = alef_norm
        self.hamza_norm = hamza_norm
        self.waw_norm = waw_norm
        self.alef_maqsura_norm = alef_maqsura_norm
        self.taa_marbuta_norm = taa_marbuta_norm
        self.normalize_indian_digits = normalize_indian_digits

    def normalize(self, text):
        norm_dict = {
            'ا': self.alef_norm,
            'أ': self.alef_norm,
            'إ': self.alef_norm,
            'آ': self.alef_norm,
            'ء': self.hamza_norm,
            'ؤ': self.waw_norm,
            'و': self.waw_norm,
            'ئ': self.alef_maqsura_norm,
            'ى\b': self.alef_maqsura_norm,
            'ي\b': self.alef_maqsura_norm,
            'ة\b': self.taa_marbuta_norm,
            'ه\b': self.taa_marbuta_norm,
        }
        text_ = text
        norm_dict = {k: v for k, v in norm_dict.items() if v is not None}
        for k, v in norm_dict.items():
            k_regex = re.compile(k)
            text_ = re.sub(k_regex, v, text_)

        return text_

class Preprocessor:
    def __init__(self, stemmer=None, normalizer=None, tokenizer=None, stop_words=None, keep_punct=False):
        self.stemmer = stemmer
        self.normalizer = normalizer
        self.tokenizer = word_tokenize if not tokenizer else tokenizer
        self.punctuation = string.punctuation if not keep_punct else ''
        self.stop_words = set() if not stop_words else set(stop_words)
        
    def is_stopword(self, word):
        return word in self.stop_words

    def remove_punct(self, word):
        trans = str.maketrans({p: ' ' for p in list(self.punctuation)})
        return word.translate(trans)
    def remove_repeated_letters(self, word):
        return re.sub(r'(\w)\1+', r'\1', word, flags=re.IGNORECASE)
        
    def striphtml(self, text): 
        cleanr = re.compile('<.*?>') 
        cleantext = re.sub(cleanr, ' ', str(text)) 
        return cleantext
    
    def stem(self, word):
        return self.stemmer.stem(word)
        
    def normalize(self, word):
        return self.normalizer.normalize(word)

    def __call__(self, text):
        processed_text = []
        text = text
        tokenized_text = self.tokenizer(text)
        for w in tokenized_text:
            w = self.remove_punct(w)
            w = self.remove_repeated_letters(w)
            if self.stemmer:
                w = self.stem(w)
            if self.normalizer:
                w = self.normalize(w)

            processed_text.append(w)
        return processed_text