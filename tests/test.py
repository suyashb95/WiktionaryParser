import unittest, json
from ..wiktionaryparser import WiktionaryParser

parser = WiktionaryParser()

class LengthTest(unittest.TestCase):
    def test_all_words(self):
        word_dict = {}
        test_dict = {
            'English': ['patronise', 'test', 'abiologically', 'alexin', 'song', 'house'],
            'Latin': ['video'],
            'Norwegian Bokmål': ['seg', 'aldersblandet', 'by', 'for', 'admiral'],
            'Swedish': ['house']
        }
        for lang, words in test_dict.items():
            parser.set_default_language(lang)
            for word in words:
                word_dict[word] = parser.fetch(word)
        print(word_dict)

if __name__ == '__main__':
    unittest.main()
