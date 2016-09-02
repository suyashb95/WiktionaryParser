class WordData(object):
    """
    Class for etymology, definitions, pronunciations and audio links
    """

    def __init__(self, etymology=None, definitions=None, pronunciations=None,
                 audio_links=None, inflections=None, translations=None):
        self.etymology = etymology if etymology else ''
        self.definition_list = definitions
        self.pronunciations = pronunciations if pronunciations else []
        self.audio_links = audio_links if audio_links else []
        self.inflections = inflections if inflections else []
        self.translations = translations if translations else []

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
        """
        converts to JSON
        """
        return {
            'etymology': self.etymology,
            'definitions': [definition.to_json() for definition in
                            self._definition_list],
            'pronunciations': self.pronunciations,
            'audioLinks': self.audio_links,
            'inflections': self.inflections,
            'translations': self.translations
        }


class Definition(object):
    """
    container class for definitions.
    """

    def __init__(self, part_of_speech=None, text=None, related_words=None,
                 example_uses=None):
        self.part_of_speech = part_of_speech if part_of_speech else ''
        self.text = text if text else ''
        self.related_words = related_words
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
        """
        converts to json.
        """
        return {
            'partOfSpeech': self.part_of_speech if self.part_of_speech else '',
            'text': self.text if self.text else '',
            'relatedWords': [
                related_word.to_json() for related_word in self.related_words]
            if self.related_words else [],
            'exampleUses': self.example_uses if self.example_uses else []
        }


class RelatedWord(object):
    """
    container class for related words.
    """

    def __init__(self, relationship_type=None, words=None):
        self.relationship_type = relationship_type if relationship_type else ''
        self.words = words if words else []

    def to_json(self):
        """
        converts to JSON.
        """
        return {
            'relationshipType': self.relationship_type if
            self.relationship_type else '',
            'words': self.words if self.words else []
        }
