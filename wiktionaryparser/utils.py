from typing import List, Optional, Union, NoReturn, Dict
from wiktionaryparser.types import Pronunciation


class RelatedWord:
    def __init__(
        self, relationship_type: Optional[str] = None, words: Optional[List[str]] = None
    ) -> None:
        self.relationship_type = relationship_type if relationship_type else ""
        self.words = words if words else []

    def to_json(self) -> Dict[str, Union[str, List[str], list]]:
        return {"relationshipType": self.relationship_type, "words": self.words}


class Definition:
    def __init__(
        self,
        part_of_speech: Optional[str] = None,
        text: Optional[str] = None,
        related_words: Optional[List[RelatedWord]] = None,
        example_uses=None,
    ) -> None:
        self.part_of_speech = part_of_speech if part_of_speech else ""
        self.text = text if text else ""
        self.related_words = related_words if related_words else []
        self.example_uses = example_uses if example_uses else []

    @property
    def related_words(self) -> Union[list, List[RelatedWord]]:
        return self._related_words

    @related_words.setter
    def related_words(self, related_words) -> Union[None, NoReturn]:
        if related_words is None:
            self._related_words = []
            return
        elif not isinstance(related_words, list):
            raise TypeError("Invalid type for relatedWord")
        else:
            for element in related_words:
                if not isinstance(element, RelatedWord):
                    raise TypeError("Invalid type for relatedWord")
            self._related_words = related_words

    def to_json(self) -> Dict[str, Union[str, list]]:
        return {
            "partOfSpeech": self.part_of_speech,
            "text": self.text,
            "relatedWords": [
                related_word.to_json() for related_word in self.related_words
            ],
            "examples": self.example_uses,
        }


class WordData:
    def __init__(
        self,
        etymology: Optional[str] = None,
        definitions: Optional[List[Definition]] = None,
        pronunciations: Pronunciation = None,
        audio_links: Optional[List[str]] = None,
    ) -> None:
        self.etymology = etymology if etymology else ""
        self.definition_list = definitions
        self.pronunciations = pronunciations if pronunciations else []
        self.audio_links = audio_links if audio_links else []

    @property
    def definition_list(self) -> List[Definition]:
        return self._definition_list

    @definition_list.setter
    def definition_list(self, definitions: List[Definition]) -> Union[None, NoReturn]:
        if definitions is None:
            self._definition_list = []
            return

        elif not isinstance(definitions, list):
            raise TypeError("Invalid type for definition")

        else:
            for element in definitions:
                if not isinstance(element, Definition):
                    raise TypeError("Invalid type for definition")
            self._definition_list = definitions

    def to_json(
        self,
    ) -> Dict[
        str,
        Union[
            str,
            List[Dict[str, Union[str, list]]],
            Dict[str, Union[Pronunciation, list]],
        ],
    ]:
        return {
            "etymology": self.etymology,
            "definitions": [
                definition.to_json() for definition in self._definition_list
            ],
            "pronunciations": {"text": self.pronunciations, "audio": self.audio_links},
        }
