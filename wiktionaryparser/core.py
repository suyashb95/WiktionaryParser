import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
import exrex
import tqdm
import copy
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
EXCLUDED_APPENDICES = [
    "obsolete"
]
def is_subheading(child, parent):
    child_headings = child.split(".")
    parent_headings = parent.split(".")
    if len(child_headings) <= len(parent_headings):
        return False
    for child_heading, parent_heading in zip(child_headings, parent_headings):
        if child_heading != parent_heading:
            return False
    return True

class WiktionaryParser(object):
    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/{}?printable=yes"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.language = 'english'
        self.current_word = None
        self.PARTS_OF_SPEECH = copy.copy(PARTS_OF_SPEECH)
        self.RELATIONS = copy.copy(RELATIONS)
        self.EXCLUDED_APPENDICES = copy.copy(EXCLUDED_APPENDICES)
        self.INCLUDED_ITEMS = self.RELATIONS + self.PARTS_OF_SPEECH + ['etymology', 'pronunciation']

    def include_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        if part_of_speech not in self.PARTS_OF_SPEECH:
            self.PARTS_OF_SPEECH.append(part_of_speech)
            self.INCLUDED_ITEMS.append(part_of_speech)

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.PARTS_OF_SPEECH.remove(part_of_speech)
        self.INCLUDED_ITEMS.remove(part_of_speech)

    def include_relation(self, relation):
        relation = relation.lower()
        if relation not in self.RELATIONS:
            self.RELATIONS.append(relation)
            self.INCLUDED_ITEMS.append(relation)

    def exclude_relation(self, relation):
        relation = relation.lower()
        self.RELATIONS.remove(relation)
        self.INCLUDED_ITEMS.remove(relation)

    def set_default_language(self, language=None):
        if language is not None:
            self.language = language.lower()

    def get_default_language(self):
        return self.language

    def clean_html(self):
        unwanted_classes = ['sister-wikipedia', 'thumb', 'reference', 'cited-source']
        for tag in self.soup.find_all(True, {'class': unwanted_classes}):
            tag.extract()

    def remove_digits(self, string):
        return string.translate(str.maketrans('', '', digits)).strip()

    def count_digits(self, string):
        return len(list(filter(str.isdigit, string)))

    def get_id_list(self, contents, content_type):
        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'definitions':
            checklist = self.PARTS_OF_SPEECH
            if self.language == 'chinese':
                checklist += self.current_word
        elif content_type == 'related':
            checklist = self.RELATIONS
        else:
            return None
        id_list = []
        if len(contents) == 0:
            return [('1', x.title(), x) for x in checklist if self.soup.find('span', {'id': x.title()})]
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = self.remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def get_word_data(self, language):
        contents = self.soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None
        for content in contents:
            if language == content.text.lower():
                start_index = content.find_previous().text + '.'
                
        if not start_index:
            if contents:
                return []
            language_heading = self.soup.find_all(
                "span",
                {"class": "mw-headline"},
                string=lambda s: s.lower() == language
            )
            if not language_heading:
                return []
        for content in contents:
            index = content.find_previous().text
            content_text = self.remove_digits(content.text.lower())
            if index.startswith(start_index) and content_text in self.INCLUDED_ITEMS:
                word_contents.append(content)
        word_data = {
            'related': self.parse_related_words(word_contents),
            'examples': self.parse_examples(word_contents),
            'definitions': self.parse_definitions(word_contents),
            'etymologies': self.parse_etymologies(word_contents),
            'pronunciations': self.parse_pronunciations(word_contents),
        }
        json_obj_list = self.map_to_object(word_data)
        for obj in json_obj_list:
            obj['categories'] = self.parse_categories()
            obj['language'] = language
            
        return json_obj_list

    def parse_categories(self):
        catlinks = self.soup.select('#mw-normal-catlinks>ul>li')
        return sorted({link.text for link in catlinks})

    def parse_pronunciations(self, word_contents):
        pronunciation_id_list = self.get_id_list(word_contents, 'pronunciation')
        pronunciation_list = []
        audio_links = []
        pronunciation_div_classes = ['mw-collapsible', 'vsSwitcher']
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            pronunciation_text = []
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
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
    
    def mine_element(self, element):
        text = element.text.strip()
        headword = element.find('strong', {"class": "headword"})
        headword = headword.text if headword else None
        appendix_removal = element.find_all("a", {"title": "Appendix:Glossary"})
        appendix_removal += element.find_all("span", {"class": "ib-content"})
        appendix_removal = [a.text for a in appendix_removal if a.text not in self.EXCLUDED_APPENDICES]

        for k in appendix_removal:
            src_regex = re.compile(f'(\({k}\)|{k})')
            text = re.sub(src_regex, '', text).strip()

        D = {
            "text": text,
            "appendix_tags": appendix_removal
        }
        return D, headword
    
    def parse_definitions(self, word_contents):
        definition_id_list = self.get_id_list(word_contents, 'definitions')
        definition_list = []
        definition_tag = None
        for def_index, def_id, def_type in definition_id_list:
            definition_text = []
            definition_headword = None
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent.find_next_sibling()
            while table and table.name not in ['h3', 'h4', 'h5']:
                definition_tag = table
                table = table.find_next_sibling()
                if definition_tag.name == 'p':
                    if definition_tag.text.strip():
                        def_dt, hw = self.mine_element(definition_tag)
                        if hw:
                            definition_headword = hw
                        def_dt['headword'] = definition_headword
                        definition_text.append(def_dt)
                if definition_tag.name in ['ol', 'ul']:
                    for element in definition_tag.find_all('li', recursive=False):
                        if element.text:
                            def_text, hw = self.mine_element(element)
                            if hw:
                                definition_headword = hw
                            def_text['headword'] = definition_headword
                            definition_text.append(def_text)
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

    def parse_etymologies(self, word_contents):
        etymology_id_list = self.get_id_list(word_contents, 'etymologies')
        etymology_list = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
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

    def parse_related_words(self, word_contents):
        relation_id_list = self.get_id_list(word_contents, 'related')
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while parent_tag and not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            if parent_tag:
                for list_tag in parent_tag.find_all('li'):
                    words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))

        #Pass 2
        id_list = {e.find_previous().text: e.parent.get('href') for e in word_contents}
        # id_list = list(id_list.items())
        for k in id_list:
            def_id = id_list[k].replace('#', '')
            content = self.soup.find(True, {"id": def_id}).parent
            while True:
                content = content.find_next_sibling()
                if content.name in ['h3', 'h4', 'h5']:
                    # print()
                    break

                nyms = content.select('.nyms')
                # print(len(nyms), end=", ")

                for nym in nyms:
                    #Find parent li
                    relation_type_span = nym.select_one('span.defdate')
                    relation_type = relation_type_span.text if relation_type_span is not None else ""
                    relation_type = re.sub('s?:$', 's', relation_type).lower()
                    if relation_type in self.RELATIONS:
                        relation_type_span.extract()
                        words = [a.get_text() for a in nym.select('span>a')]
                        related_words_list.append((k, words, relation_type))

        print(len(related_words_list))
        return related_words_list

    def map_to_object(self, word_data):
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]
            for pronunciation_index, text, audio_links in word_data['pronunciations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(pronunciation_index)) or (current_etymology[0] <= pronunciation_index < next_etymology[0]):
                    data_obj.pronunciations = text
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in word_data['definitions']:
                current_etymology_str = ".".join(f"{int(num):02d}" for num in current_etymology[0].split(".") if num)
                definition_index_str = ".".join(f"{int(num):02d}" for num in definition_index.split(".") if num)
                next_etymology_str = ".".join(f"{int(num):02d}" for num in next_etymology[0].split(".") if num)
                if current_etymology_str <= definition_index_str < next_etymology_str \
                        or is_subheading(current_etymology[0], definition_index):
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if related_word_index.startswith(definition_index):
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    data_obj.definition_list.append(def_obj)
            json_obj_list.append(data_obj.to_json())
        return json_obj_list

    def fetch(self, word, language=None, old_id=None, query=None):
        language = self.language if not language else language
        languages = language if hasattr(language, '__iter__') and type(language) != str else [language]
        response = self.session.get(self.url.format(word), params={'oldid': old_id})
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.current_word = word
        self.clean_html()
        res = []
        for lang in languages:
            res += self.get_word_data(lang.lower())
        for obj in res:
            obj['query'] = obj.get('query', word) if query is None else query
            obj['word'] = obj.get('query', word)

        return res

    def fetch_all_potential(self, word, language=None, old_id=None, verbose=0):
        def get_possible_altenrnatives(word):
            replacement_dict = {
                "ا": ["ا", "أ", "إ", "آ"]
            }
            replacement_dict = {k: f"({'|'.join(v)})" for k, v in replacement_dict.items()}

            trans = str.maketrans(replacement_dict)
            word_regex = word.translate(trans)

            return list(exrex.generate(word_regex))
        
        possible_altenrnatives = get_possible_altenrnatives(word)

        res = {word: self.fetch(word)}
        if verbose > 0:
            possible_altenrnatives = tqdm.tqdm(possible_altenrnatives, desc="Fetching potential forms", leave=False)

        for w in possible_altenrnatives:
            if verbose > 0:
                possible_altenrnatives.set_postfix(w)

            fetch_res = self.fetch(w, language=language, old_id=old_id, query=word)
            if fetch_res:
                res[w] = fetch_res
        return res