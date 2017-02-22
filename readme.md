###Wiktionary Parser

A python project which parses word content from Wiktionary in an easy to use JSON format.
Right now, it parses etymologies, definitions, pronunciations, examples, audio links and related words.


####JSON structure

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
        "text": "definition text",
        "partOfSpeech": "part of speech",
        "examples": ["list of examples"]
    }],
    "etymology": "etymology text",
}]
```

####Installation

#####Using pip 
* run `pip install wiktionaryparser`

#####From Source
* Clone the repo or download the zip
* `cd` to the folder
* run `pip install -r "requirements.txt"`

####Usage

 - Import the WiktionaryParser class.
 - Initialize an object and use the fetch("word", "language") method.
 - The default language is English.
 - The default language can be changed using the set_default_language method.

####Examples

```python
>>> from wiktionaryparser import WiktionaryParser
>>> parser = WiktionaryParser()
>>> word = parser.fetch('test')
>>> another_word = parser.fetch('test', 'french')
>>> parser.set_default_language('french')
```

####Requirements

 - requests==2.7.0
 - beautifulsoup4==4.4.0

####Contributions

If you want to add features/improvement or report issues, feel free to send a pull request!
