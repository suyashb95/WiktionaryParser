class WordData(object):
    def __init__(self, etymology=None, definitions=None, pronunciations=None,
                 audio_links=None):
        self.etymology = etymology if etymology else ''
        self.definition_list = definitions
        self.pronunciations = pronunciations if pronunciations else []
        self.audio_links = audio_links if audio_links else []

    @property
    def definition_list(self):
        return self._definition_list

    @definition_list.setter
    def definition_list(self, definitions):
        if definitions is None:
            self._definition_list = []
            return
        elif not isinstance(definitions, list):
            raise TypeError('Invalid type for definition')
        else:
            for element in definitions:
                if not isinstance(element, Definition):
                    raise TypeError('Invalid type for definition')
            self._definition_list = definitions

    def to_json(self):
        return {
            'etymology': self.etymology,
            'definitions': [definition.to_json() for definition in self._definition_list],
            'pronunciations': {
                'text': self.pronunciations,
                'audio': self.audio_links
            }
        }


class Definition(object):
    def __init__(self, part_of_speech = None, text = None, related_words = None, example_uses = None):
        self.part_of_speech = part_of_speech if part_of_speech else ''
        self.text = text if text else ''
        self.related_words = related_words if related_words else []
        self.example_uses = example_uses if example_uses else []

    @property
    def related_words(self):
        return self._related_words

    @related_words.setter
    def related_words(self, related_words):
        if related_words is None:
            self._related_words = []
            return
        elif not isinstance(related_words, list):
            raise TypeError('Invalid type for relatedWord')
        else:
            for element in related_words:
                if not isinstance(element, RelatedWord):
                    raise TypeError('Invalid type for relatedWord')
            self._related_words = related_words

    def to_json(self):
        return {
            'partOfSpeech': self.part_of_speech,
            'text': self.text,
            'relatedWords': [related_word.to_json() for related_word in self.related_words],
            'examples': self.example_uses 
        }


class RelatedWord(object):
    def __init__(self, relationship_type=None, words=None):
        self.relationship_type = relationship_type if relationship_type else ''
        self.words = words if words else []

    def to_json(self):
        return {
            'relationshipType': self.relationship_type,
            'words': self.words
        }