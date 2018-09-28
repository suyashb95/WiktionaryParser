import unittest, json
from .context import WiktionaryParser
from deepdiff import DeepDiff

parser = WiktionaryParser()

class TestParser(unittest.TestCase):
    def test_multiple_languages(self):
        sample_output = {}
        with open('tests/testOutput.json', 'r') as f:
            sample_output = json.load(f)
        words_to_test = {
            'English': {'grapple': 50080840, 'test': 50342756, 'patronise': 49023308, 'abiologically': 43781266, 'alexin': 50152026, 'song': 50235564, 'house': 50356446},
            'Latin': {'video': 50291344},
            'Norwegian Bokmål': {'seg': 50359832, 'aldersblandet': 38616917, 'by': 50399022, 'for': 50363295, 'admiral': 50357597, 'heis': 49469949, 'konkurs': 48269433, 'pantergaupe': 46717478, 'maldivisk': 49859434},
            'Swedish': {'house': 50356446},
            'Ancient Greek': {'ἀγγελία': 47719496}
        }
        for lang, words in words_to_test.items():
            parser.set_default_language(lang)
            for word, oldid in words.items():
                parsed_word = parser.fetch(word, oldid=oldid)
                print("Testing \"{}\" in {}".format(word, lang))
                self.assertEqual(DeepDiff(parsed_word, sample_output[lang][word], ignore_order=True), {})

    def test_actual_or_archived(self):
        self.assertEqual(parser.get_url('grapple', None), 'https://en.wiktionary.org/wiki/grapple?printable=yes')
        self.assertEqual(parser.get_url('grapple', 50080840), 'https://en.wiktionary.org/wiki/grapple?printable=yes&oldid=50080840')
        self.assertNotEqual(parser.fetch('grapple'), parser.fetch('grapple', oldid=50080840))

if __name__ == '__main__':
    unittest.main()
