from pkg_resources import get_distribution
__version__ = get_distribution("wiktionaryparser").version

from wiktionaryparser.utils import WordData, Definition, RelatedWord
from wiktionaryparser.core import WiktionaryParser


__all__ = [
    'WordData',
    'Definition',
    'RelatedWord',
    'WiktionaryParser'
]
