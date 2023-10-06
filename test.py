from parameterized import parameterized
import unittest
import json
from wiktionaryparser import WiktionaryParser
from deepdiff import DeepDiff
from typing import Dict, List
import mock
from urllib import parse
import os

parser = WiktionaryParser()


tests_dir = os.path.dirname(__file__)+"\\tests"
html_test_files_dir = os.path.join(tests_dir, 'html_test_files')
markup_test_files_dir = os.path.join(tests_dir, 'markup_test_files')

test_words = [
    # ('ἀγγελία', 47719496, ['Ancient Greek']),
    ('اللغة_العربية', None, ['Arabic', 'EngliSH']),
    # ('grapple', 50080840, ['EnGlish']),
    # ('test', 50342756, ['English']),
    # ('patronise', 49023308, ['English']),
    # ('abiologically', 43781266, ['English']),
    # ('alexin', 50152026, ['English']),
    # ('song', 60388804, ['English']),
    # ('house', 50356446, ['English']),
    # ('correspondent', 61052028, ['English']),
    # ('video', 50291344, ['Latin']),
    # ('seg', 50359832, ['Norwegian Bokmål']),
    # ('aldersblandet', 38616917, ['Norwegian Bokmål']),
    # ('by', 50399022, ['Norwegian Bokmål']),
    # ('for', 50363295, ['Norwegian Bokmål']),
    # ('admiral', 50357597, ['Norwegian Bokmål']),
    # ('heis', 49469949, ['Norwegian Bokmål']),
    # ('konkurs', 48269433, ['Norwegian Bokmål']),
    # ('pantergaupe', 46717478, ['Norwegian Bokmål']),
    # ('maldivisk', 49859434, ['Norwegian Bokmål']),
    # ('house', 50356446, ['Swedish'])
]


def get_test_words_table(*allowed_words):
    """Convert the test_words array to an array of three element tuples."""
    result = []

    for word, old_id, languages in test_words:
        for language in languages:
            if len(allowed_words) == 0 or (word in allowed_words):
                result.append((language, word, old_id))

    return result

test_words = get_test_words_table()

parser = WiktionaryParser()
for lang, word, old_id in test_words:
    result = parser.fetch(word=word, language=lang, old_id=old_id)
    print(json.dumps(result, indent=4, ensure_ascii=False))
