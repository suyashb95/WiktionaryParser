###Wiktionary Parser

A python project which parses word content from Wiktionary in an easy to use JSON format.
Right now, it parses etymologies, definitions, pronunciations, examples, audio links and related words.


####JSON structure

```json
[{
    "pronunciations": ["list of pronunciations"],
    "definitions": [{
        "relatedWords": [{
            "relationshipType": "word relationship type",
            "words": ["list of related words"]
        }],
        "text": "definition text",
        "partOfSpeech": "part of speech",
        "exampleUses": ["list of examples"]
    }],
    "etymology": "etymology text",
    "audioLinks": ["list of audio pronunciation links"]
}]
```

####Usage

 - Download the zip or clone the repo.
 - `cd` to the folder.
 - Import the WiktionaryParser class from WikiParse
 - Initialize an object and use the fetch("word", "language") method.
 - The default language is English.
 - The default language can be changed using the setDefaultLanguage method.

####Examples

```python
>>> from WikiParse import WiktionaryParser
>>> parser = WiktionaryParser()
>>> word = parser.fetch('test')
>>> another_word = parser.fetch('test','french')
>>> parser.setDefaultLanguage('french')
```

####Requirements

 - requests==2.7.0
 - beautifulsoup4==4.4.0

####Contributions

If you want to add features/improvement or report issues, feel free to send a pull request!
