from WikiParse import WiktionaryParser
import unittest

parser = WiktionaryParser()


class LengthTest(unittest.TestCase):
    """
    Tests if all data is being parsed correctly.
    """

    def test_1(self):
        """
        1) Etymology as a list or paragraph.
        2) Related words common to all definitions.
        3) Multiple etymologies and definitions with no related words.
        4) Pronunciations and audio links common to all etymologies.
        """
        word = parser.fetch('set')
        self.assertTrue(len(word) == 2)
        self.assertTrue(len(word[0]['etymology'].strip().split('\n')) == 2)
        self.assertTrue(len(word[0]['definitions']) == 3)
        self.assertTrue(len(word[0]['pronunciations']) == 4)
        self.assertTrue(len(word[0]['audioLinks']) == 1)
        self.assertTrue(len(word[1]['etymology'].strip().split('\n')) == 1)
        self.assertTrue(len(word[1]['definitions']) == 2)
        self.assertTrue(len(word[1]['pronunciations']) == 4)
        self.assertTrue(len(word[1]['audioLinks']) == 1)
        for definition in word[0]['definitions']:
            if definition['partOfSpeech'] == 'verb':
                self.assertTrue(
                    len(definition['text'].strip().split('\n')) == 42)
                for related_words in definition['relatedWords']:
                    if related_words['relationshipType'] == 'derived terms':
                        self.assertTrue(len(related_words['words']) == 56)
            if definition['partOfSpeech'] == 'noun':
                self.assertTrue(
                    len(definition['text'].strip().split('\n')) == 17)
                for related_words in definition['relatedWords']:
                    if related_words['relationshipType'] == 'derived terms':
                        self.assertTrue(len(related_words['words']) == 27)
            if definition['partOfSpeech'] == 'adjective':
                self.assertTrue(
                    len(definition['text'].strip().split('\n')) == 8)
                for related_words in definition['relatedWords']:
                    if related_words['relationshipType'] == 'synonyms':
                        self.assertTrue(len(related_words['words']) == 3)
                    if related_words['relationshipType'] == 'derived terms':
                        self.assertTrue(len(related_words['words']) == 27)

    def test_2(self):
        """
        1) Single etymology with single definition.
        """
        word = parser.fetch('song')
        self.assertTrue(len(word) == 1)
        self.assertTrue(len(word[0]['etymology'].strip().split('\n')) == 1)
        self.assertTrue(len(word[0]['definitions']) == 1)
        self.assertTrue(len(word[0]['pronunciations']) == 3)
        self.assertTrue(len(word[0]['audioLinks']) == 1)
        for definition in word[0]['definitions']:
            if definition['partOfSpeech'] == 'noun':
                self.assertTrue(
                    len(definition['text'].strip().split('\n')) == 8)
                for related_words in definition['relatedWords']:
                    if related_words['relationshipType'] == 'derived terms':
                        self.assertTrue(len(related_words['words']) == 15)

    def test_3(self):
        """
        1) Multiple pronunciations with each etymology.
        """
        word = parser.fetch('house')
        self.assertTrue(len(word) == 2)
        self.assertTrue(len(word[0]['pronunciations']) == 4)
        self.assertTrue(len(word[1]['pronunciations']) == 0)

    def test_r(self):
        """
        1) Testing in different languages.
        """
        word = parser.fetch('house', 'swedish')
        self.assertTrue(len(word) == 1)
        self.assertTrue(word[0]['etymology'] == '')
        self.assertTrue(len(word[0]['definitions']) == 1)
        self.assertTrue(word[0]['pronunciations'] == [])
        self.assertTrue(word[0]['audioLinks'] == [])


if __name__ == '__main__':
    unittest.main()
