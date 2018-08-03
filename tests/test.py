import unittest, json
from ..wiktionaryparser import WiktionaryParser
from deepdiff import DeepDiff

parser = WiktionaryParser()

class TestParser(unittest.TestCase): 
    def test_multiple_languages(self):
        sample_output = None
        with open('./wiktionaryparser/tests/testOutput.json', 'r') as f:
            sample_output = json.load(f)
        words_to_test = {
            'English': ['patronise', 'test', 'abiologically', 'alexin', 'song', 'house'],
            'Latin': ['video'],
            'Norwegian Bokmål': ['seg', 'aldersblandet', 'by', 'for', 'admiral'],
            'Swedish': ['house']
        }
        for lang, words in words_to_test.items():
            parser.set_default_language(lang)
            for word in words:
                parsed_word = parser.fetch(word)[0]
                print("Testing \"{}\" in {}".format(word, lang))
                self.assertEqual(DeepDiff(parsed_word, sample_output[lang][word], ignore_order=True), {})

if __name__ == '__main__':
    unittest.main()
