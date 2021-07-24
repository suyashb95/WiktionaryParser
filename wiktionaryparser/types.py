from typing import Optional, List


class Pronunciation:
    def __init__(
        self, texts: Optional[List[str]] = None, audios: Optional[List[str]] = None
    ) -> None:
        self.texts = texts
        self.audios = audios

    def __getitem__(self, item):
        # Provides '.' lookup as well as dictionary style lookup
        return getattr(item)
