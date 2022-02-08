from parameterized import parameterized
import unittest
import json
from wiktionaryparser import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict, List
from unittest import mock
from urllib import parse
import os

parser = WiktionaryParser(language="français")


tests_dir = os.path.dirname(__file__)
html_test_files_dir = os.path.join(tests_dir, 'html_test_files_fr')
output_test_json = os.path.join(tests_dir, "testOutput_fr.json")

test_words = [
    ('anarchie', 20220207, ['Français']),
    ('anarchie', 20220207, ['Italien']),
    ('échelle', 20220207, ['Français']),
    ('roquefort', 20220207, ['Français']),
    ('song', 20220207, ['Anglais']),
]


def get_test_words_table(*allowed_words):
    """Convert the test_words array to an array of three element tuples."""
    result = []

    for word, old_id, languages in test_words:
        for language in languages:
            if len(allowed_words) == 0 or (word in allowed_words):
                result.append((language, word, old_id))

    return result


class MockResponse:
    def __init__(self, text: str):
        self.text = text


def mocked_requests_get(*args, **kwargs):
    url = args[0]
    parsed_url = parse.urlparse(url)
    params = kwargs['params']
    
    word = parsed_url.path.split('/')[-1]
    filepath = os.path.join(html_test_files_dir,
                            f'{word}-{params["oldid"]}.html')
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    return MockResponse(text)


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.expected_results = {}

        with open(output_test_json, 'r') as f:
            self.expected_results = json.load(f)

        super(TestParser, self).__init__(*args, **kwargs)

    @parameterized.expand(get_test_words_table())
    @mock.patch("requests.Session.get", side_effect=mocked_requests_get)
    def test_fetch_using_mock_session(self, lang: str, word: str, old_id: int, mock_get):
        self.__test_fetch(lang, word, old_id)

    def __test_fetch(self, lang: str, word: str, old_id: int):
        fetched_word = parser.fetch(word, language=lang, old_id=old_id)

        print("Testing \"{}\" in \"{}\"".format(word, lang))
        expected_result = self.expected_results[lang][word]

        diff = DeepDiff(fetched_word,
                        expected_result,
                        ignore_order=True)

        if diff != {}:
            print("Found mismatch in \"{}\" in \"{}\"".format(word, lang))
            print(json.dumps(json.loads(diff.to_json()), indent=4))
            print("Actual result:")
            print(json.dumps(fetched_word, indent=4))

        self.assertEqual(diff, {})


if __name__ == '__main__':
    unittest.main()
