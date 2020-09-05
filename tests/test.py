from parameterized import parameterized
import unittest
import json
from .context import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict

parser = WiktionaryParser()


test_words_dict = {
    'Ancient Greek': [
        ('ἀγγελία', 47719496),
    ],
    'English': [
        ('grapple', 50080840),
        ('test', 50342756),
        ('patronise', 49023308),
        ('abiologically', 43781266),
        ('alexin', 50152026),
        ('song', 50235564),
        ('house', 50356446),
    ],
    'Latin': [
        ('video', 50291344),
    ],
    'Norwegian Bokmål': [
        ('seg', 50359832),
        ('aldersblandet', 38616917),
        ('by', 50399022),
        ('for', 50363295),
        ('admiral', 50357597),
        ('heis', 49469949),
        ('konkurs', 48269433),
        ('pantergaupe', 46717478),
        ('maldivisk', 49859434),
    ],
    'Swedish': [
        ('house', 50356446)
    ]
}


def get_test_words_table():
    """Convert the test words dict to an array of three element tuples."""
    result = []

    for lang, word_and_old_ids in test_words_dict.items():
        for word, old_id in word_and_old_ids:
            result.append((lang, word, old_id))

    return result


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.expected_results = {}

        with open('tests/testOutput.json', 'r') as f:
            self.expected_results = json.load(f)

        super(TestParser, self).__init__(*args, **kwargs)

    @parameterized.expand(get_test_words_table())
    def test_fetch(self, language: str, word: str, old_id: int):
        self.__test_fetch(language, word, old_id)

    def __test_fetch(self, lang: str, word: str, old_id: int):
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
