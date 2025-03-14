import re
from nltk.tokenize import word_tokenize
import string
from bidi.algorithm import get_display
import unicodedata as ud

class Normalizer:
    # Normalize the hamza, the waw, the alef-maqsura, taa-marbuta, indian numbers (configurable attrs)
    def __init__(self, hamza_norm=None, waw_norm=None, alef_norm=None, alef_maqsura_norm=None, taa_marbuta_norm=None, normalize_indian_digits=False):
        self.alef_norm = alef_norm
        self.hamza_norm = hamza_norm
        self.waw_norm = waw_norm
        self.alef_maqsura_norm = alef_maqsura_norm
        self.taa_marbuta_norm = taa_marbuta_norm
        self.normalize_indian_digits = normalize_indian_digits
        
    def normalize_punct(self, text):
        trans = str.maketrans({
            "؟": "?",
            "،": ",",
            "؛": ";",
            "…": "...",
            "”": '"',
            "“": '"'
        })
        processed_text = text.translate(trans)
        return processed_text
    
    def normalize_arabic_numbers(self, text):
        trans = str.maketrans({
            "١": "1",
            "٢": "2",
            "٣": "3",
            "٤": "4",
            "٥": "5",
            "٦": "6",
            "٧": "7",
            "٨": "8",
            "٩": "9",
            "٠": "0",
        })
        processed_text = text.translate(trans)
        return processed_text
    
    def __call__(self, text):
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
        text_ = self.normalize_punct(text_)
        text_ = self.normalize_arabic_numbers(text_)
        norm_dict = {k: v for k, v in norm_dict.items() if v is not None}
        for k, v in norm_dict.items():
            k_regex = re.compile(k)
            text_ = re.sub(k_regex, v, text_)

        return text_

class Preprocessor:
    def __init__(self, return_type="list", stemmer=None, normalizer=None, tokenizer=None, stop_words=None, 
                 hashtag_replacement='', mention_replacement='',
                 keep_punct=False, keep_numbers=False, keep_latin=False, 
                 keep_shakl=False, keep_emojis=False
                 ):
        self.stemmer = stemmer
        self.normalizer = normalizer if normalizer is not None else Normalizer()
        self.tokenize = word_tokenize if not tokenizer else tokenizer
        self.punctuation = string.punctuation if not keep_punct else ''
        self.stop_words = set() if not stop_words else set(stop_words)
        self.return_type = return_type
        self.keep_shakl = keep_shakl
        self.keep_emojis = keep_emojis
        self.keep_latin = keep_latin
        self.keep_numbers = keep_numbers
        self.mention_replacement = mention_replacement
        self.hashtag_replacement = hashtag_replacement
    
    def is_stopword(self, word):
        return word in self.stop_words
    
    def remove_punct(self, word):
        trans = str.maketrans({p: ' ' for p in list(self.punctuation)})
        return word.translate(trans)
    
    def remove_repeated_letters(self, word):
        return re.sub(r'(\w)\1{2,}', r'\1', word, flags=re.IGNORECASE)
        
    def striphtml(self, text): 
        cleanr = re.compile('<.*?>') 
        cleantext = re.sub(cleanr, ' ', str(text)) 
        return cleantext
    
    def stripurl(self, text): 
        cleanr = re.compile('https?://\w+(.\w+)+(/?\w+)*') 
        cleantext = re.sub(cleanr, ' ', str(text)) 
        return cleantext
    
    def stem(self, word):
        return self.stemmer.stem(word)
        
    def normalize(self, word):
        return self.normalizer(word)

    def strip_shakl(self, word):
        shakl_regex = re.compile(r'[\u064B-\u0655]')
        word = re.sub(shakl_regex, '', word)
        return word
    
    def strip_tatweel(self, word):
        shakl_regex = re.compile(r'[ـ]')
        word = re.sub(shakl_regex, '', word)
        return word
    
    def strip_emojis(self, word):
        emoji_regex = re.compile(r'[\u263a-\U0001f645]')
        word = re.sub(emoji_regex, '', word)
        return word
    
    def strip_spaces(self, word):
        word = re.sub('(\s)\1\1+', '\1', word)
        return word.strip()
    
    def __call__(self, text):
        processed_text = []
        text = self.stripurl(text)
        text = self.striphtml(text)
        if self.hashtag_replacement is not None:
            text = re.sub(r'#\w+', str(self.hashtag_replacement), text)
        if self.mention_replacement is not None:
            text = re.sub(r'@\w+', str(self.mention_replacement), text)
        # text = text
        # text = text
        tokenized_text = self.tokenize(text)
        for w in tokenized_text:
            if not self.keep_emojis:
                w = self.strip_emojis(w)
            
            
            w = self.remove_repeated_letters(w)
            w = self.strip_tatweel(w)
            if self.stemmer:
                w = self.stem(w)
            if self.normalizer:
                w = self.normalize(w)
            w = self.remove_punct(w)
            if not self.keep_shakl:
                w = self.strip_shakl(w)
            if not self.keep_numbers:
                w = re.sub('[0-9]', ' ', w)
            if not self.keep_latin:
                w = re.sub('[A-Za-z]', ' ', w)
            w = self.strip_spaces(w)

            processed_text.append(w)
        if self.return_type == "str" and not isinstance(processed_text, str):
            processed_text = " ".join(processed_text)
        return processed_text