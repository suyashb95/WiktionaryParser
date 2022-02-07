#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Language tools, to change the language in the WiktionaryParser class
"""

ABBREVIATION_TO_LANGUAGE = {
    'en': 'english', 
    "fr": 'français',
    }

LANGUAGES = {
    "english": {
        "ETYMOLOGIES_HEADER": [
            'etymology',
            ],
        "PRONUNCIATION_HEADER": [
            'pronunciation',
            ],
        "PART_OF_SPEECH": [
            "noun", "verb", "adjective", "adverb", "determiner",
            "article", "preposition", "conjunction", "proper noun",
            "letter", "character", "phrase", "proverb", "idiom",
            "symbol", "syllable", "numeral", "initialism", "interjection",
            "definitions", "pronoun", "particle", "predicative", "participle",
            "suffix",
            ],
        "RELATIONS": [
            "synonyms", "antonyms", "hypernyms", "hyponyms",
            "meronyms", "holonyms", "troponyms", "related terms",
            "coordinate terms",
            ],
        "URL": "https://en.wiktionary.org/wiki/{}?printable=yes",
        },
    "français": {
        "ETYMOLOGIES_HEADER": [
            'étymologie',
            ],
        "PRONUNCIATION_HEADER": [
            'prononciation',
            ],
        "PART_OF_SPEECH": [
            "nom commun", "verbe", "adjectif", "adverbe", "déterminant",
            "article", "preposition", "conjonction", "nom propre",
            "lettre", "caractère", "expression", "proverbe", "idiome",
            "symbole", "syllabe", "nombre", "acronyme", "interjection",
            "définitions", "pronom", "particule", "prédicat", "participe",
            "suffixe", "locution nominale",
            ],
        "RELATIONS": [
            "synonymes", "antonymes", "hypéronymes", "hyponymes",
            "méronymes", "holonymes", "paronymes", "troponymes",
            "vocabulaire apparenté par le sens", "dérivés",
            "anagrammes", "proverbes et phrases toutes faites",
            "apparentés étymologiques", "quasi-synonymes",
            ],
        "URL": "https://fr.wiktionary.org/wiki/{}?printable=yes",
        },    
}

def abbreviation_to_language(language="en"):
    """In case one gives an international code (e.g. 'en' for England/English),
    this method transforms the international code to the language name, 
    according to the dictionnary `COUNTRY_TO_LANGUAGE`, (e.g. returns "english")
    """
    try:
        language = ABBREVIATION_TO_LANGUAGE[language]
    except KeyError: 
        pass
    return language

def get_language(language="english"):
    """Exports the part of speech, relations, etymology, 
    pronunciation and url of the given language, according to the 
    LANGUAGES dictionnary above."""
    pos = LANGUAGES.get(language, {}).get("PART_OF_SPEECH", [])
    rel = LANGUAGES.get(language, {}).get("RELATIONS", [])
    ety = LANGUAGES.get(language, {}).get("ETYMOLOGIES_HEADER", [])
    pronun = LANGUAGES.get(language, {}).get("PRONUNCIATION_HEADER", [])
    url = LANGUAGES.get(language, {}).get("URL", "")
    return pos, rel, ety, pronun, url
