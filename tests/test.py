from parameterized import parameterized
import unittest
import json
from .context import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict

parser = WiktionaryParser()


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.expected_results = {}

        with open('tests/testOutput.json', 'r') as f:
            self.expected_results = json.load(f)

        super(TestParser, self).__init__(*args, **kwargs)

    @parameterized.expand([
        ('grapple', 50080840),
        ('test', 50342756),
        ('patronise', 49023308),
        ('abiologically', 43781266),
        ('alexin', 50152026),
        ('song', 50235564),
        ('house', 50356446),
    ])
    def test_words_from_english(self, word: str, old_id: int):
        self.__test_word(word, old_id, 'English')

    @parameterized.expand([
        ('video', 50291344),
    ])
    def test_words_from_latin(self, word: str, old_id: int):
        self.__test_word(word, old_id, 'Latin')

    @parameterized.expand([
        ('seg', 50359832),
        ('aldersblandet', 38616917),
        ('by', 50399022),
        ('for', 50363295),
        ('admiral', 50357597),
        ('heis', 49469949),
        ('konkurs', 48269433),
        ('pantergaupe', 46717478),
        ('maldivisk', 49859434),
    ])
    def test_words_from_norwegian_bokmal(self, word: str, old_id: int):
        self.__test_word(word, old_id, 'Norwegian Bokmål')

    @parameterized.expand([
        ('house', 50356446)
    ])
    def test_words_from_swedish(self, word: str, old_id: int):
        self.__test_word(word, old_id, 'Swedish')

    @parameterized.expand([
        ('ἀγγελία', 47719496)
    ])
    def test_words_from_ancient_greek(self, word: str, old_id: int):
        self.__test_word(word, old_id, 'Ancient Greek')

    def __test_words(self, words_and_ids: Dict[str, int], lang: str):
        for word, old_id in words_and_ids.items():
            self.__test_word(word, old_id, lang)

    def __test_word(self, word: str, old_id: int, lang: str):
        parser.set_default_language(lang)
        fetched_word = parser.fetch(word, old_id=old_id)

        print("Testing \"{}\" in \"{}\"".format(word, lang))
        expected_result = self.expected_results[lang][word]

        diff = DeepDiff(fetched_word,
                        expected_result,
                        ignore_order=True)

        if diff != {}:
            print("Found mismatch in \"{}\" in \"{}\"".format(word, lang))
            print(json.dumps(json.loads(diff.json), indent=4))
            print("Actual result:")
            print(json.dumps(fetched_word, indent=4))

        self.assertEqual(diff, {})


if __name__ == '__main__':
    unittest.main()
 	