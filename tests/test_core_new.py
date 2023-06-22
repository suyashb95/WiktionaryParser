"""A few quick tests of the modifications made by bjkeefe to core.py.  
These tests will NOT all succeed if run against the master branch of WiktionaryParser,
at least as of 2023-06-17.
"""
try:
    import pytest
except ModuleNotFoundError:
    print("test_core_new.py: these tests require pytest to be importable, so this won't work:")
    print("    $ py test_core_new.py")
    print()
    print("However, pytest usually comes along for the ride when installing Python from")
    print("python.org, so this should work:")
    print("    $ pytest test_core_new.py")
    raise SystemExit()

from wiktionaryparser import WiktionaryParser


def test_core_new_default_language():
    parser = WiktionaryParser()

    # A word that has several English definitions
    result = parser.fetch("receive")
    assert type(result) == list
    assert len(result) == 1
    assert type(result[0]) == dict
    assert "etymology" in result[0]
    assert "pronunciations" in result[0]
    assert "definitions" in result[0]
    assert len(result[0]["definitions"]) > 0
    assert "additional_info" not in result[0]
    
    # A word that has a Wiktionary entry, because it is a common misspelling
    result = parser.fetch("recieve")
    assert type(result) == list
    assert len(result) == 1
    assert type(result[0]) == dict
    assert "etymology" in result[0]
    assert "pronunciations" in result[0]
    assert "definitions" in result[0]
    assert len(result[0]["definitions"]) > 0
    assert "additional_info" not in result[0]

    # Two words that have a Wiktionary entry, but no English definitions
    for word in ["abilitanti", "aimai"]:
        result = parser.fetch(word)
        assert type(result) == list
        assert len(result) == 1
        assert type(result[0]) == dict
        assert "etymology" not in result[0]
        assert "pronunciations" not in result[0]
        assert "definitions" not in result[0]
        assert "additional_info" in result[0]
        assert result[0]["additional_info"] == f"no english entry for {word}"

    # A "word" that has no Wiktionary entry
    result = parser.fetch("aimiable")
    assert type(result) == list
    assert len(result) == 1
    assert type(result[0]) == dict
    assert "etymology" not in result[0]
    assert "pronunciations" not in result[0]
    assert "definitions" not in result[0]
    assert "additional_info" in result[0]
    assert result[0]["additional_info"] == f"Wiktionary does not yet have an entry for aimiable"


def test_core_new_non_english_languages():
    words = ["receive", "recieve", "abilitanti", "aimai", "aimiable"]
    languages = ["italian", "french", "japanese"]

    parser = WiktionaryParser()
    for word in words:
        for language in languages:
            parser.set_default_language(language)
            result = parser.fetch(word)
            if language == "italian":
                if word == "abilitanti":
                    assert "definitions" in result[0]
                    assert "additional_info" not in result[0]
                else:
                    assert "definitions" not in result[0]
                    assert "additional_info" in result[0]
                    if word != "aimiable":
                        assert result[0]["additional_info"] == f"no {language} entry for {word}"
                    else:
                        expected = f"Wiktionary does not yet have an entry for {word}"
                        assert result[0]["additional_info"] == expected

            elif language == "french" or language == "japanese":
                if word == "aimai":
                    assert "definitions" in result[0]
                    assert "additional_info" not in result[0]
                else:
                    assert "definitions" not in result[0]
                    assert "additional_info" in result[0]
                    if word != "aimiable":
                        assert result[0]["additional_info"] == f"no {language} entry for {word}"
                    else:
                        expected = f"Wiktionary does not yet have an entry for {word}"
                        assert result[0]["additional_info"] == expected

                            
