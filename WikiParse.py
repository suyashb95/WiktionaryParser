'''
Final code for wiktionary parser.
Have to make a class.
'''
import requests, re
from utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup as BS
PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism"
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

class WiktionaryParser(object):
    '''
    Final class for Wiktionary parser.
    '''

    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
    @staticmethod
    def getIDList(contents, content_type):
        '''
        Returns a list of IDs relating to the specific content type.
        Text can be obtained by parsing the text within span tags having those IDs.
        '''
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
        IDList = []
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = ''.join([i for i in content_tag.text \
            if not i.isdigit()]).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                IDList.append((content_index, content_id, text_to_check))
        return IDList
    def getWordData(self, language):
        '''
        Hardcoded to get Enlglish content.
        Have to change later.
        Match language, get previous tag, get starting number.
        '''
        contents = self.soup.findAll('span', {'class':'toctext'})
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
        etymology_id_list = self.getIDList(word_contents, 'etymologies')
        definition_id_list = self.getIDList(word_contents, 'definitions')
        relation_id_list = self.getIDList(word_contents, 'related')
        pronunciation_id_list = self.getIDList(word_contents, 'pronunciation')
        etymology_list = self.parseEtymologies(etymology_id_list)
        example_list = self.parseExamples(definition_id_list)
        definition_list = self.parseDefinitions(definition_id_list)
        related_words_list = self.parseRelatedWords(relation_id_list)
        pronunciation_list = self.parsePronunciations(pronunciation_id_list)
        json_obj_list = self.makeClass(
            etymology_list,
            definition_list,
            example_list,
            related_words_list,
            pronunciation_list
            )
        return json_obj_list
    def parsePronunciations(self, pronunciation_id_list=None):
        '''
        Parse pronunciations from their IDs.
        clear supertext tags first.
        separate audio links.
        '''
        pronunciation_list = []
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            span_tag = self.soup.findAll('span', {'id':pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.findNextSibling()
            for super_tag in list_tag.findAll('sup'):
                super_tag.clear()
            audio_links = []
            pronunciation_text = []
            for list_element in list_tag.findAll('li'):
                for audio_tag in list_element.findAll('div', {'class':'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    list_element.clear()
                if list_element.text:
                    pronunciation_text.append(list_element.text.encode('utf-8'))
            pronunciation_list.append((pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list
    def parseDefinitions(self, definition_id_list=None):
        '''
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses and all.
        '''
        definition_list = []
        for definition_index, definition_id, definition_type in definition_id_list:
            span_tag = self.soup.findAll('span', {'id':definition_id})[0]
            table = span_tag.parent
            definition_tag = None
            while table.name != 'ol':
                definition_tag = table
                table = table.findNextSibling()
            definition_text = (definition_tag.text) + '\n'
            for element in table.findAll('li'):
                definition_text += element.text
            definition_text = re.sub('(\\n+)', '\\n', \
            definition_text).strip()
            definition_list.append((definition_index, \
            definition_text.encode('utf-8'), definition_type))
        return definition_list
    def parseExamples(self, definition_id_list=None):
        '''
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses and all.
        <ul> tags have biblical references, remove them.
        '''
        example_list = []
        for definition_index, definition_id, definition_type in definition_id_list:
            span_tag = self.soup.findAll('span', {'id':definition_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.findNextSibling()
            for element in table.findAll('ul'):
                element.clear()
            examples = []
            for element in table.findAll('dd'):
                example_text = element.text.strip()
                if example_text and not (example_text.startswith('(') \
                and example_text.endswith(')')):
                    examples.append(example_text.encode('utf-8'))
                element.clear()
            example_list.append((definition_index, examples, definition_type))
        return example_list
    def parseEtymologies(self, etymology_id_list=None):
        '''
        Word etymology is either a para or a list.
        move forward till you find either.
        '''
        etymology_list = []
        for etymology_index, etymology_id, _ in etymology_id_list:
            span_tag = self.soup.findAll('span', {'id':etymology_id})[0]
            etymology_tag = None
            next_tag = span_tag.parent.findNextSibling()
            while next_tag.name not in ['h3', 'h4']:
                etymology_tag = next_tag
                next_tag = next_tag.findNextSibling()
            if etymology_tag is None:
                etymology_text = ''
            elif etymology_tag.name == 'p':
                etymology_text = (etymology_tag.text)
            else:
                etymology_text = ''
                for list_tag in etymology_tag.findAll('li'):
                    etymology_text += (list_tag.text) + '\n'
            etymology_list.append((etymology_index, etymology_text.encode('utf-8')))
        return etymology_list
    def parseRelatedWords(self, relation_id_list=None):
        '''
        Look for parent tags with <li> tags, those are related words.
        <li> tags can either be in tables or lists.
        '''
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.findAll('span', {'id':related_id})[0]
            parent_tag = span_tag.parent
            while not parent_tag.findAll('li'):
                parent_tag = parent_tag.findNextSibling()
            for list_tag in parent_tag.findAll('li'):
                words.append(list_tag.text.encode('utf-8'))
            related_words_list.append((related_index, words, relation_type))
        return related_words_list
    @staticmethod
    def makeClass(etymology_list,
                  definition_list,
                  example_list,
                  related_words_list,
                  pronunciation_list
                 ):
        '''
        Takes all the data and makes classes.
        '''
        json_obj_list = []
        for etymology_index, etymology_text in etymology_list:
            data_obj = WordData()
            data_obj.etymology = etymology_text
            for pronunciation_index, pronunciations, audio_links in pronunciation_list:
                if pronunciation_index.startswith(etymology_index) \
                or pronunciation_index.count('.') == 1:
                    data_obj.pronunciations = pronunciations
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in definition_list:
                if definition_index.startswith(etymology_index) or definition_index.count('.') == 1:
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in example_list:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in related_words_list:
                        if related_word_index.startswith(definition_index) \
                        or related_word_index.count('.') == 2:
                            related_word_obj = RelatedWord()
                            related_word_obj.words = related_words
                            related_word_obj.relationship_type = relation_type
                            def_obj.related_words.append(related_word_obj)
                    data_obj.definition_list.append(def_obj)
            json_obj_list.append(data_obj.toJSON())
        return json_obj_list
    def fetch(self, word, language="english"):
        '''
        main function.
        subject to change.
        '''
        response = self.session.get(self.url + word + '?printable=yes')
        self.soup = BS(response.text, 'html.parser')
        return self.getWordData(language.lower())
