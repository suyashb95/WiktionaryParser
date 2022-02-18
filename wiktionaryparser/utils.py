def count_digits(s):
    return len(list(filter(str.isdigit, s)))


class WordData(object):
    def __init__(self, index, next_index):
        self.index = index
        self.next_index = next_index
        self.data = dict()

    def contains_heading(self, other_index):
        current_index_str = ".".join(f"{int(num):02d}" for num in self.index.split(".") if num)
        definition_index_str = ".".join(f"{int(num):02d}" for num in other_index.split(".") if num)
        next_index_str = ".".join(f"{int(num):02d}" for num in self.next_index.split(".") if num)
        return current_index_str <= definition_index_str < next_index_str

    def is_sibling_heading(self, other):
        return count_digits(self.index) == count_digits(other)

    def belongs_to_heading(self, parent):
        child_headings = self.index.split(".")
        parent_headings = parent.split(".")
        if len(child_headings) <= len(parent_headings):
            return False
        for child_heading, parent_heading in zip(child_headings, parent_headings):
            if child_heading != parent_heading:
                return False
        return True


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