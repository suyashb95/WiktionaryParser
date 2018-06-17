"""
Final code for wiktionary parser.
"""
from __future__ import unicode_literals
from __future__ import absolute_import
import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest

PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection", "definitions"
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "derived terms", "coordinate terms",
]

UNWANTED_LIST = [
    'External links', 'Compounds',
    'Anagrams', 'References', "Further reading"
    'Statistics', 'See also', 'Usage notes',
]

class WiktionaryParser(object):
    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/{}?printable=yes"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.language = 'english'
        self.current_word = None

    def set_default_language(self, language=None):
        if language is not None:
            self.language = language.lower()

    def get_default_language(self):
        return self.language

    def get_id_list(self, contents, content_type):
        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'definitions':
            checklist = PARTS_OF_SPEECH
            if self.language == 'chinese':
                checklist += self.current_word
        elif content_type == 'related':
            checklist = RELATIONS
        else:
            return None
        id_list = []
        if len(contents) == 0:
            return [('1', x.title(), x) for x in checklist if self.soup.find('span', {'id': x.title()})]
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = ''.join(i for i in content_tag.text if not i.isdigit()).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def get_word_data(self, language):
        try:
            self.soup.find('div', {'class': 'sister-wikipedia sister-project noprint floatright'}).decompose()
        except:
            pass
        contents = self.soup.find_all('span', {'class': 'toctext'})
        language_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        for content in contents:
            index = content.find_previous().text
            if index.startswith(start_index):
                language_contents.append(content)
        word_contents = []
        for content in language_contents:
            if content.text not in UNWANTED_LIST:
                word_contents.append(content)
        word_data = {
            'examples': self.parse_examples(word_contents),
            'definitions': self.parse_definitions(word_contents),
            'etymologies': self.parse_etymologies(word_contents),
            'related': self.parse_related_words(word_contents),
            'pronunciations': self.parse_pronunciations(word_contents),
        }
        json_obj_list = self.map_to_object(word_data)
        return json_obj_list

    def parse_pronunciations(self, word_contents):
        pronunciation_id_list = self.get_id_list(word_contents, 'pronunciation')
        pronunciation_list = []
        audio_links = []
        pronunciation_text = []
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
                if list_tag.name == 'p':
                    pronunciation_text.append(list_tag.text)
                    break
                if list_tag.name == 'div' and 'mw-collapsible' in list_tag['class']:
                    break
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all(
                        'div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    audio_tag.extract()
                for nested_list_element in list_element.find_all('ul'):
                    nested_list_element.extract()
                if list_element.text:
                    pronunciation_text.append(list_element.text)
            pronunciation_list.append((pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list

    def parse_definitions(self, word_contents):
        definition_id_list = self.get_id_list(word_contents, 'definitions')
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
                definition_text += re.sub('(\\n+)', '', element.text.strip()) + '\n'
            if def_type == 'definitions':
                def_type = ''
            definition_list.append((def_index, definition_text, def_type))
        return definition_list

    def parse_examples(self, word_contents):
        definition_id_list = self.get_id_list(word_contents, 'definitions')
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            examples = []
            while table and table.name == 'ol':
                for element in table.find_all(['dd', 'ul']):
                    example_text = element.text.strip()
                    if example_text and not (example_text.startswith('(') and example_text.endswith(')')):
                        examples.append(example_text)
                    element.clear()
                example_list.append((def_index, examples, def_type))
                table = table.find_next_sibling()
        return example_list

    def parse_etymologies(self, word_contents):
        etymology_id_list = self.get_id_list(word_contents, 'etymologies')
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

    def parse_related_words(self, word_contents):
        relation_id_list = self.get_id_list(word_contents, 'related')
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

    def map_to_object(self, word_data):
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue='999'):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]
            for pronunciation_index, text, audio_links in word_data['pronunciations']:
                if current_etymology[0] < pronunciation_index < next_etymology[0]:
                    data_obj.pronunciations = text
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in word_data['definitions']:
                if current_etymology[0] < definition_index < next_etymology[0]:
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if current_etymology[0] < related_word_index < next_etymology[0]:
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    data_obj.definition_list.append(def_obj)
            json_obj_list.append(data_obj.to_json())
        return json_obj_list

    def fetch(self, word, language=None):
        language = self.language if not language else language
        response = self.session.get(self.url.format(word))
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.current_word = word
        return self.get_word_data(language.lower())
