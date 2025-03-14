from .utils import WordData, Definition, RelatedWord
from .core import PARTS_OF_SPEECH, RELATIONS, WiktionaryParser
from .preprocessing import *
__all__ = [
    'WordData',
    'Definition',
    'RelatedWord',
    'PARTS_OF_SPEECH',
    'RELATIONS',
    'WiktionaryParser',
    'Normalizer',
    'Preprocessor'
]
