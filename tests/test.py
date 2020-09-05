from parameterized import parameterized
import unittest
import json
from .context import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict

parser = WiktionaryParser()


test_words = [
    ('ἀγγελία', 47719496, ['Ancient Greek']),
    ('grapple', 50080840, ['English']),
    ('test', 50342756, ['English']),
    ('patronise', 49023308, ['English']),
    ('abiologically', 43781266, ['English']),
    ('alexin', 50152026, ['English']),
    ('song', 50235564, ['English']),
    ('house', 50356446, ['English']),
    ('video', 50291344, ['Latin']),
    ('seg', 50359832, ['Norwegian Bokmål']),
    ('aldersblandet', 38616917, ['Norwegian Bokmål']),
    ('by', 50399022, ['Norwegian Bokmål']),
    ('for', 50363295, ['Norwegian Bokmål']),
    ('admiral', 50357597, ['Norwegian Bokmål']),
    ('heis', 49469949, ['Norwegian Bokmål']),
    ('konkurs', 48269433, ['Norwegian Bokmål']),
    ('pantergaupe', 46717478, ['Norwegian Bokmål']),
    ('maldivisk', 49859434, ['Norwegian Bokmål']),
    ('house', 50356446, ['Swedish'])
]


def get_test_words_table():
    """Convert the test_words array to an array of three element tuples."""
    result = []

    for word, old_id, languages in test_words:
        for language in languages:
            result.append((language, word, old_id))

    return result


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.expected_results = {}

        with open('tests/testOutput.json', 'r') as f:
            self.expected_results = json.load(f)

        super(TestParser, self).__init__(*args, **kwargs)

    @parameterized.expand(get_test_words_table())
    def test_fetch(self, lang: str, word: str, old_id: int):
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
