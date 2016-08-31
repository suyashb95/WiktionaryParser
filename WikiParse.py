"""
Final code for wiktionary parser.
"""
from __future__ import unicode_literals
import re, requests, sys
sys.path.append(".")
from utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
import unittest

PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection"
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "derived terms", "coordinate terms"
]

UNWANTED_LIST = [
    'External links',
    'Anagrams', 'References',
    'Statistics', 'See also'
]

INFLECTIONS_FORMS = {
    "en": ["infinitive", "present participle", "past participle"]
}

TRANSLATIONS_LIST = {
    "en": "Translations"
}

class WiktionaryParser(object):
    """
    Final class for Wiktionary parser.
    """

    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://",
                           requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://",
                           requests.adapters.HTTPAdapter(max_retries=2))
        self.language = 'english'

    def set_default_language(self, language=None):
        """
        Sets the default language of the parser object.
        """
        if language is not None:
            self.language = language.lower()
        return

    def get_default_language(self):
        """
        returns the default language of the object.
        """
        return self.language

    @staticmethod
    def get_id_list(contents, content_type):
        """
        Returns a list of IDs relating to the specific content type.
        Text can be obtained by parsing the text within span tags
        having those IDs.
        """
        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'definitions':
            checklist = PARTS_OF_SPEECH
        elif content_type == 'related':
            checklist = RELATIONS
        else:
            return None
        id_list = []
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = ''.join(i for i in content_tag.text
                                    if not i.isdigit()).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def get_word_data(self, language):
        """
        Match language, get previous tag, get starting number.
        """
        contents = self.soup.find_all('span', {'class': 'toctext'})
        language_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if start_index is None:
            return []
        for content in contents:
            index = content.find_previous().text
            if index.startswith(start_index):
                language_contents.append(content)
        word_contents = []
        for content in language_contents:
            if content.text not in UNWANTED_LIST:
                word_contents.append(content)
        etymology_id_list = self.get_id_list(word_contents, 'etymologies')
        definition_id_list = self.get_id_list(word_contents, 'definitions')
        relation_id_list = self.get_id_list(word_contents, 'related')
        pronunciation_id_list = self.get_id_list(word_contents, 'pronunciation')
        etymology_list = self.parse_etymologies(etymology_id_list)
        example_list = self.parse_examples(definition_id_list)
        definition_list = self.parse_definitions(definition_id_list)
        related_words_list = self.parse_related_words(relation_id_list)
        pronunciation_list = self.parse_pronunciations(pronunciation_id_list)
        inflection_list = self.parse__inflections() # AM 2016-08-31: Added inflections
        posList = []
        for d in definition_list:
            for pos in d:
                if pos in PARTS_OF_SPEECH:
                    posList.append(pos)
        translation_list = self.parse_translations(posList) # and translations by PoS

        json_obj_list = self.make_class(
            etymology_list,
            definition_list,
            example_list,
            related_words_list,
            pronunciation_list,
            inflection_list,
            translation_list
        )

        return json_obj_list

    def parse_pronunciations(self, pronunciation_id_list=None):
        """
        Parse pronunciations from their IDs.
        clear supertext tags first.
        separate audio links.
        """
        pronunciation_list = []
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            audio_links = []
            pronunciation_text = []
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all(
                        'div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    list_element.clear()
                if list_element.text:
                    pronunciation_text.append(list_element.text)
            pronunciation_list.append(
                (pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list

    def parse_definitions(self, definition_id_list=None):
        """
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses.
        """
        definition_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            definition_tag = None
            while table.name != 'ol':
                definition_tag = table
                table = table.find_next_sibling()
            definition_text = definition_tag.text + '\n'
            for element in table.find_all('li'):
                definition_text += re.sub('(\\n+)', '',
                                          element.text.strip()) + '\n'
            definition_list.append((def_index,
                                    definition_text,
                                    def_type))
        return definition_list

    def parse_examples(self, definition_id_list=None):
        """
        look for <dd> tags inside <ol> tags.
        remove data in <ul> tags.
        """
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            for element in table.find_all('ul'):
                element.clear()
            examples = []
            for element in table.find_all('dd'):
                example_text = element.text.strip()
                if example_text and not (example_text.startswith('(') and
                                         example_text.endswith(')')):
                    examples.append(example_text)
                element.clear()
            example_list.append((def_index, examples, def_type))
        return example_list

    def parse_etymologies(self, etymology_id_list=None):
        """
        Word etymology is either a para or a list.
        move forward till you find either.
        """
        etymology_list = []
        for etymology_index, etymology_id, _ in etymology_id_list:
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            etymology_tag = None
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag.name not in ['h3', 'h4', 'div']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
            if etymology_tag is None:
                etymology_text = ''
            elif etymology_tag.name == 'p':
                etymology_text = etymology_tag.text
            else:
                etymology_text = ''
                for list_tag in etymology_tag.find_all('li'):
                    etymology_text += list_tag.text + '\n'
            etymology_list.append(
                (etymology_index, etymology_text))
        return etymology_list

    def parse_related_words(self, relation_id_list=None):
        """
        Look for parent tags with <li> tags, those are related words.
        <li> tags can either be in tables or lists.
        """
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            for list_tag in parent_tag.find_all('li'):
                words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))
        return related_words_list

    def parse__inflections(self):
        """
        Look for conjugation table and try to parse it getting inflected forms
        """
        infTable = self.soup.find("table", {"class": "inflection-table"})
        if infTable is None:
            return {}
        inflections = dict()
        for tr in infTable.find_all("tr"):
            try:
                form = tr.find_all("th")[0].text
                if form in INFLECTIONS_FORMS["en"]:
                    inflections[form] = tr.find_all("td")[0].text
            except:
                pass
        return inflections

    def parse_translations(self, pos_list):
        translations = dict()
        for i, pos in enumerate(pos_list):
            idTrans = TRANSLATIONS_LIST["en"] if i==0 else TRANSLATIONS_LIST["en"]+"_{}".format(i+1)
            transHeader = self.soup.find_all("span", {'id': idTrans})
            print "I've {} tables".format(len(transHeader))
            try:
                nextTag = transHeader[0].parent.next_sibling#.next_sibling
            except IndexError:
                # There is not translations in da page
                continue
            while True:
                try:
                    if nextTag.name == "div":
                        nextTag.get('class')
                        if nextTag['class'] == [u'NavFrame']:
                            transTable = nextTag.find("table")
                            break
                except TypeError as ex:
                    # If catched is because there is not a proper object
                    pass
                nextTag = nextTag.next_sibling
            translations[pos] = dict()
            # print "For pos {} I have:".format(pos.decode('utf-8')), transTable
            for li in transTable.find_all("li"):
                for span in li.find_all("span"):
                    try:
                        lang = span['lang'].decode('utf-8')
                        text = span.a.text.decode('utf-8')
                        # print lang.encode('utf-8'), text.encode('utf-8')
                        if lang in translations:
                            translations[pos][lang].append(text)
                        else:
                            translations[pos][lang] = [text]
                        # break
                    except:
                        pass
        return translations

    @staticmethod
    def make_class(etymology_list,
                   definition_list,
                   example_list,
                   related_words_list,
                   pronunciation_list,
                   inflection_list,
                   translation_list
                  ):
        """
        Takes all the data and makes classes.
        """
        json_obj_list = []
        if not etymology_list:
            etymology_list = [('', '')]
        for etymology_index, etymology_text in etymology_list:
            data_obj = WordData()
            data_obj.etymology = etymology_text
            for pronunciation_index, pronunciations, audio_links in pronunciation_list:
                if pronunciation_index.startswith(etymology_index) \
                or pronunciation_index.count('.') == etymology_index.count('.'):
                    data_obj.pronunciations = pronunciations
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in definition_list:
                if definition_index.startswith(etymology_index) \
                or definition_index.count('.') == etymology_index.count('.'):
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in example_list:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in related_words_list:
                        if related_word_index.startswith(definition_index) \
                        or (related_word_index.startswith(etymology_index) \
                        and related_word_index.count('.') == definition_index.count('.')):
                            words = None
                            try:
                                words = next(
                                    item.words for item in def_obj.related_words
                                    if item.relationship_type == relation_type)
                            except StopIteration:
                                pass
                            if words is not None:
                                words += related_words
                                break
                            related_word_obj = RelatedWord()
                            related_word_obj.words = related_words
                            related_word_obj.relationship_type = relation_type
                            def_obj.related_words.append(related_word_obj)
                    data_obj.definition_list.append(def_obj)
                    data_obj.inflections = inflection_list # AM: 31/08/16 - Added inflection list to object
                    data_obj.translations = translation_list # and translations by PoS
            json_obj_list.append(data_obj.to_json())
        return json_obj_list

    def fetch(self, word, language=None):
        """
        main function.
        subject to change.
        """
        language = self.language if not language else language
        response = self.session.get(self.url + word + '?printable=yes')
        self.soup = BeautifulSoup(response.text, 'html.parser')
        return self.get_word_data(language.lower())


class TestConjugationParsing(unittest.TestCase):

    # def test_posExtractoin(self):
    #     parser = WiktionaryParser()
    #     word = parser.fetch("pick")
    #     pos = [d["partOfSpeech"] for d in word[0]["definitions"]]
    #     self.assertEqual([u'noun', u'verb'], pos)
    #     word = parser.fetch("eat")
    #     pos = [d["partOfSpeech"] for d in word[0]["definitions"]]
    #     self.assertEqual([u'verb'], pos)

    def test_getTranslations(self):
        parser = WiktionaryParser()
        word = parser.fetch("pick")
        print word[0]["translations"]

if __name__ == '__main__':

    if sys.argv[1] == 'test':
        print "Running in test mode"
        sys.argv = sys.argv[:1]
        unittest.main()
