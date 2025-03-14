### Wiktionary Parser

A python project which downloads words from English Wiktionary ([en.wiktionary.org](https://en.wiktionary.org)) and parses articles' content in an easy to use JSON format. Right now, it parses etymologies, definitions, pronunciations, examples, audio links and related words.

Note: This project will not be maintained since there are many free dictionary APIs now, please see - https://dictionaryapi.dev/ for example

[![Downloads](http://pepy.tech/badge/wiktionaryparser)](http://pepy.tech/project/wiktionaryparser)

#### JSON structure

```json
[{
    "pronunciations": {
        "text": ["pronunciation text"],
        "audio": ["pronunciation audio"]
    },
    "definitions": [{
        "relatedWords": [{
            "relationshipType": "word relationship type",
            "words": ["list of related words"]
        }],
        "text": ["list of definitions"],
        "partOfSpeech": "part of speech",
        "examples": ["list of examples"]
    }],
    "etymology": "etymology text",
}]
```

#### Installation

##### Using pip
* run `pip install wiktionaryparser`

##### From Source
* Clone the repo or download the zip
* `cd` to the folder
* run `pip install -r "requirements.txt"`

#### Usage

 - Import the WiktionaryParser class.
 - Initialize an object and use the `fetch("word", "language")` method.
 - The default language is English, it can be changed using the `set_default_language method`.
 - Include/exclude parts of speech to be parsed using `include_part_of_speech(part_of_speech)` and `exclude_part_of_speech(part_of_speech)`
 - Include/exclude relations to be parsed using `include_relation(relation)` and `exclude_relation(relation)`

#### Examples

```python
>>> from wiktionaryparser import WiktionaryParser
>>> parser = WiktionaryParser()
>>> word = parser.fetch('test')
>>> another_word = parser.fetch('test', 'french')
>>> parser.set_default_language('french')
>>> parser.exclude_part_of_speech('noun')
>>> parser.include_relation('alternative forms')
```

```python
>>> word, categories = parser.fetch('test', return_categories=True)
>>> words = parser.fetch_category('English phrasebook')
>>> words, subcategories = parser.fetch_category('English phrasebook', 
                                                  return_subcategories=True)
```

#### Requirements

 - requests==2.20.0
 - beautifulsoup4==4.4.0

#### Contributions

If you want to add features/improvement or report issues, feel free to send a pull request!

#### License

Wiktionary Parser is licensed under [MIT](LICENSE.txt).
