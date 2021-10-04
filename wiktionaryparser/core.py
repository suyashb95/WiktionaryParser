import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits

PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection",
    "definitions", "pronoun", "particle", "predicative", "participle",
    "suffix",
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "coordinate terms",
]


def remove_digits(string):
    return string.translate(str.maketrans('', '', digits)).strip()


__metaclass__ = type


class ContentParser(object):
    """
    Superclass for parser objects. A parser is responsible for parsing a part of a Wiktionary content page.
    """

    def parse_content(self, soup, language, word_contents):
        """
        Use the given HTML soup to parse parts of the word contents for the given language
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_id_list(self, soup, contents, checklist):
        """
        Utility function useful for parsers to retrieve the ids of content tags. The function will try
        to find content tags containing the text snippets, either as id or as content text. For example, including the
        text snippet 'noun' in the checklist, causes the result to include the id of the 'Noun' content tag if it is
        present in the contents.
        """
        id_list = []
        if len(contents) == 0:
            return [('1', text_to_check.title(), text_to_check) for text_to_check in checklist if
                    soup.find('span', {'id': text_to_check.title()})]
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list


class PronunciationParser(ContentParser):
    def parse_content(self, soup, language, word_contents):
        pronunciation_id_list = self.get_id_list(soup, word_contents, ['pronunciation'])
        pronunciation_list = []
        audio_links = []
        pronunciation_div_classes = ['mw-collapsible', 'vsSwitcher']
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            pronunciation_text = []
            span_tag = soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
                if list_tag.name == 'p':
                    pronunciation_text.append(list_tag.text)
                    break
                if list_tag.name == 'div' and any(_ in pronunciation_div_classes for _ in list_tag['class']):
                    break
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all('div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    audio_tag.extract()
                for nested_list_element in list_element.find_all('ul'):
                    nested_list_element.extract()
                if list_element.text and not list_element.find('table', {'class': 'audiotable'}):
                    pronunciation_text.append(list_element.text.strip())
            pronunciation_list.append((pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list


class DefinitionsParser(ContentParser):
    def __init__(self, parts_of_speech):
        super(DefinitionsParser, self).__init__()
        self.parts_of_speech = parts_of_speech

    def parse_content(self, soup, language, word_contents):
        definition_id_list = self.get_id_list(soup, word_contents, self.parts_of_speech)
        definition_list = []
        definition_tag = None
        for def_index, def_id, def_type in definition_id_list:
            definition_text = []
            span_tag = soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent.find_next_sibling()
            while table and table.name not in ['h3', 'h4', 'h5']:
                definition_tag = table
                table = table.find_next_sibling()
                if definition_tag.name == 'p':
                    if definition_tag.text.strip():
                        definition_text.append(definition_tag.text.strip())
                if definition_tag.name in ['ol', 'ul']:
                    for element in definition_tag.find_all('li', recursive=False):
                        if element.text:
                            definition_text.append(element.text.strip())
            if def_type == 'definitions':
                def_type = ''
            definition_list.append((def_index, definition_text, def_type))
        return definition_list


class ExamplesParser(ContentParser):
    def __init__(self, parts_of_speech):
        super(ExamplesParser, self).__init__()
        self.parts_of_speech = parts_of_speech

    def parse_content(self, soup, language, word_contents):
        definition_id_list = self.get_id_list(soup, word_contents, self.parts_of_speech)
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            examples = []
            while table and table.name == 'ol':
                for element in table.find_all('dd'):
                    example_text = re.sub(r'\([^)]*\)', '', element.text.strip())
                    if example_text:
                        examples.append(example_text)
                    element.clear()
                example_list.append((def_index, examples, def_type))
                for quot_list in table.find_all(['ul', 'ol']):
                    quot_list.clear()
                table = table.find_next_sibling()
        return example_list


class EtymologiesParser(ContentParser):
    def parse_content(self, soup, language, word_contents):
        etymology_id_list = self.get_id_list(soup, word_contents, ['etymology'])
        etymology_list = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = soup.find_all('span', {'id': etymology_id})[0]
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag and next_tag.name not in ['h3', 'h4', 'div', 'h5']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                if etymology_tag.name == 'p':
                    etymology_text += etymology_tag.text
                else:
                    for list_tag in etymology_tag.find_all('li'):
                        etymology_text += list_tag.text + '\n'
            etymology_list.append((etymology_index, etymology_text))
        return etymology_list


class RelatedWordsParser(ContentParser):
    def __init__(self, relations):
        super(RelatedWordsParser, self).__init__()
        self.relations = relations

    def parse_content(self, soup, language, word_contents):
        relation_id_list = self.get_id_list(soup, word_contents, self.relations)
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while parent_tag and not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            if parent_tag:
                for list_tag in parent_tag.find_all('li'):
                    words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))
        return related_words_list


class EtymologyProcessor(object):
    def process_word_data(self, words, word_data):
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]

        etymology_pairs = list(
            zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')))

        for (current_etymology, next_etymology) in etymology_pairs:
            data_obj = WordData(current_etymology[0], next_etymology[0])
            data_obj.data["etymology"] = current_etymology[1]
            words.append(data_obj)


class PronunciationProcessor(object):
    def process_word_data(self, words, word_data):
        for word in words:
            word.data["pronunciations"] = dict()
            word.data["pronunciations"]["text"] = []
            word.data["pronunciations"]["audio"] = []
            for pronunciation_index, text, audio_links in word_data['pronunciations']:
                if word.is_sibling_heading(pronunciation_index) or word.contains_heading(pronunciation_index):
                    word.data["pronunciations"]["text"] = text
                    word.data["pronunciations"]["audio"] = audio_links


class DefinitionsProcessor(object):
    def process_word_data(self, words, word_data):
        for word in words:
            definition_list = []
            for definition_index, definition_text, definition_type in word_data['definitions']:
                if word.contains_heading(definition_index) or word.belongs_to_heading(definition_index):
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if related_word_index.startswith(definition_index):
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    definition_list.append(def_obj)
            word.data["definitions"] = [definition.to_json() for definition in definition_list]


def clean_html(soup):
    unwanted_classes = ['sister-wikipedia', 'thumb', 'reference', 'cited-source']
    for tag in soup.find_all(True, {'class': unwanted_classes}):
        tag.extract()


class WiktionaryParser(object):
    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/{}?printable=yes"
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
        self.language = 'english'
        self.parts_of_speech = set(copy(PARTS_OF_SPEECH))
        self.relations = set(copy(RELATIONS))
        self.parsers = {
            'examples': ExamplesParser(self.parts_of_speech),
            'definitions': DefinitionsParser(self.parts_of_speech),
            'etymologies': EtymologiesParser(),
            'related': RelatedWordsParser(self.relations),
            'pronunciations': PronunciationParser(),
        }
        self.processors = [EtymologyProcessor(), PronunciationProcessor(), DefinitionsProcessor()]

    def set_content_parser(self, content_name, parser):
        self.parsers[content_name] = parser

    def add_post_processor(self, processor):
        self.processors.append(processor)

    def include_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.parts_of_speech.add(part_of_speech)

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.parts_of_speech.remove(part_of_speech)

    def include_relation(self, relation):
        relation = relation.lower()
        self.relations.add(relation)

    def exclude_relation(self, relation):
        relation = relation.lower()
        self.relations.remove(relation)

    def set_default_language(self, language=None):
        if language is not None:
            self.language = language.lower()

    def get_default_language(self):
        return self.language

    def get_word_data(self, word, soup, language):
        contents = soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if not start_index:
            if contents:
                return []
            language_heading = soup.find_all(
                "span",
                {"class": "mw-headline"},
                string=lambda s: s.lower() == language
            )
            if not language_heading:
                return []

        for content in contents:
            index = content.find_previous().text
            if index.startswith(start_index):
                word_contents.append(content)

        word_data = dict()

        chinese_word_added = False
        if language == 'chinese' and word not in self.parts_of_speech:
            self.parts_of_speech.add(word)
            chinese_word_added = True

        for content_name in self.parsers:
            word_data[content_name] = self.parsers[content_name].parse_content(soup, language, word_contents)

        if chinese_word_added:
            self.parts_of_speech.remove(word)

        words = []
        for processor in self.processors:
            processor.process_word_data(words, word_data)

        return list([w.data for w in words])

    def fetch(self, word, language=None, old_id=None):
        language = self.language if not language else language
        response = self.session.get(self.url.format(word), params={'oldid': old_id})
        soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        clean_html(soup)
        return self.get_word_data(word, soup, language.lower())
