import re, requests
from .utils import WordData, Definition, RelatedWord
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
        self.__base_url = "https://en.wiktionary.org"
        self.url = self.__base_url + "/wiki/{}?printable={}"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.language = 'english'
        self.use_printable = 'yes'
        self.current_word = None
        self.current_url = None
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

    def get_word_data(self, language, include_dialects=True):
        contents = self.soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_indices = []
        json_obj_list = []
        for content in contents:
            ctl = content.text.lower()
            if language == ctl or (include_dialects and language in ctl):
                start_indices.append((content.find_previous().text + '.', ctl))
                
        if not start_indices:
            if contents:
                return []
            language_heading = self.soup.find_all(
                "span",
                {"class": "mw-headline"},
                string=lambda s: language in str(s).lower()
            )
            if not language_heading:
                return []
        for start_index, dialect in start_indices:
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
            json_obj_list_ = self.map_to_object(word_data)
            for obj in json_obj_list_:
                obj['categories'] = self.parse_categories()
                obj['language'] = dialect
            json_obj_list += json_obj_list_
            
        return json_obj_list

    def parse_categories(self):
        catlinks = self.soup.select('#mw-normal-catlinks>ul>li')
        return sorted({link.text for link in catlinks})


    def parse_examples(self, word_contents):
        definition_id_list = self.get_id_list(word_contents, 'definitions')
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table and table.name == 'ol':
                table = table.find_next_sibling()
            examples = []
            while table and table.name == 'ol':
                for element in table.find_all('dd'):
                    example_text = re.sub(r'\([^)]*\)', '', element.text.strip())
                    if example_text:
                        example = {
                            "quotation": element.select_one("*.e-quotation"),
                            "transliteration": element.select_one("*.e-transliteration"),
                            "translation": element.select_one("*.e-translation"),
                        }
                        example = {k: v.text if v is not None else v for k, v in example.items()}
                        example.update({
                            "example_text": example_text,
                        })
                        if example.get('quotation') is not None:
                            examples.append(example)
                    # element.clear()
                example_list.append((def_index, examples, def_type))
                # for quot_list in table.find_all(['ul', 'ol']):
                #     quot_list.clear()
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
        raw_text = element.text.strip()
        headword = element.find('strong', {"class": "headword"})
        headword = headword.text if headword else None
        if len(element.contents) == 1 and element.find('span', {"class": "headword-line"}, recursive=False):
            return None, headword

        text = element.text.strip()
        appendix = element.find_all("a", {"title": "Appendix:Glossary"})
        appendix += element.find_all("span", {"class": "ib-content"})
        appendix_removal = []
        example_tags = element.select("div.citation-whole")
        examples = []

        for e in example_tags:
            parent_el = e.find_parent('ul')
            for t in ['ul', 'ol']:
                parent_el = e.find_parent(t)
                if parent_el is not None:
                    break
            if parent_el is None:
                continue
            parent_el = parent_el.parent
            if parent_el == element:
                example_text = re.sub(r'\([^)]*\)', '', e.text.strip())
                if example_text:
                    example = {
                        "source": e.select_one("span.cited-source"),
                        "quotation": e.select_one("*.e-quotation"),
                        "transliteration": e.select_one("*.e-transliteration"),
                        "translation": e.select_one("*.e-translation"),
                    }
                    example = {k: v.text if v is not None else v for k, v in example.items()}
                    example.update({
                        "example_text": example_text,
                    })
                    if example.get('quotation') is not None:
                        examples.append(example)
        # print(len(examples))

        for a in appendix:
            if a.text not in self.EXCLUDED_APPENDICES:
                appendix_removal.append(a.text)
                a.extract()

        mentions = []
        remaining_a = element.find_all('a')
        for m in remaining_a:
            m_href = m.get('href')
            language = m.parent.get('lang')
            if m_href is not None:
                if m_href.startswith('/wiki'):
                    mentions.append({
                        "wikiUrl": m_href,
                        "word": m.text,
                        "language": language
                    })


        for k in appendix_removal:
            src_regex = f'(\({k}\)|{k})'
            src_regex = src_regex.replace('+', '\\+')
            src_regex = re.compile(src_regex)
            text = re.sub(src_regex, '', text).strip()
        D = {
            "raw_text": raw_text,
            "text": text,
            "appendix_tags": appendix_removal,
            "mentions": mentions,
            "examples": examples,
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
                scrappable = []
                if definition_tag.name == 'p':
                    if definition_tag.text.strip():
                        scrappable.append(definition_tag)
                        
                if definition_tag.name in ['ol', 'ul']:
                    for element in definition_tag.find_all('li', recursive=False):
                        if element.text:
                            scrappable.append(element)
                            for subelement in element.select('ol>li', recursive=False):
                                if subelement.text:
                                    scrappable.append(subelement)

                for i_scrp, e in enumerate(scrappable):
                    def_dt, hw = self.mine_element(e)
                    if hw:
                        definition_headword = hw
                    if def_dt is None:
                        continue
                    def_dt['headword'] = definition_headword
                    def_dt['def_k'] = (def_index, def_id, i_scrp)
                    definition_text.append(def_dt)
      
                    
            if def_type == 'definitions':
                def_type = ''
            definition_list.append((def_index, definition_text, def_type))
        return definition_list

    def parse_related_words(self, word_contents):
        relation_id_list = self.get_id_list(word_contents, 'related')
        id_list = {e.find_previous().text: {
            "related_section" :e.parent.get('href').replace('#', '')
        } for e in word_contents}
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while parent_tag and not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            if parent_tag:
                for i_li, list_tag in enumerate(parent_tag.find_all('li')):
                    prev_def = parent_tag
                    def_text = None
                    while True:
                        prev_def_ = prev_def.find_previous_sibling()
                        if prev_def_ is None:
                            break
                        prev_def = prev_def_
                        if prev_def.name in ['p', 'ol', 'ul']:
                            break
                    if prev_def.name == "p":
                        def_text = prev_def
                    elif prev_def.name in ['ul', 'ol']:
                        def_text = prev_def.find_all('li')[-1]
                    if def_text is not None:
                        def_text = def_text.get_text()
                    else:
                        def_text = ''
                    rel = {
                        "words": list_tag.text,
                        "def_text": def_text,
                        'def_k': (related_index, related_id, i_li)
                    }

                    words.append(rel)
            related_words_list.append((related_index, words, relation_type))

        #Pass 2
        
        # id_list = list(id_list.items())
        for k in id_list:
            def_id = id_list[k].get('related_section')
            content = self.soup.find(True, {"id": def_id}).parent
            while True:
                content = content.find_next_sibling()
                if content is None:
                    break

                elif content.name in ['h3', 'h4', 'h5']:
                    break

                elif content.name in ['ol', 'ul']:
                    lis = content.find_all('li', recursive=False)
                    for i_li, li in enumerate(lis):
                        related_words_list += self.parse_related_words_from_nyms(li, k, def_text=li.text, def_k=(k, def_id, i_li))
                elif content.name in ['p']:
                    related_words_list += self.parse_related_words_from_nyms(content, k, def_text=content.text, def_k=(k, def_id, 0))
                             
        return related_words_list
    
    def parse_related_words_from_nyms(self, content, related_index, **kwargs):
        nyms_list = []
        nyms = content.select('.nyms')
        for nym in nyms:
            relation_type_span = nym.select_one('span.defdate')
            relation_type = relation_type_span.text if relation_type_span is not None else ""
            relation_type = re.sub('s?:$', 's', relation_type).lower()
            if relation_type in self.RELATIONS:
                relation_type_span.extract()
                words = []
                for a in nym.select('span>a'):
                    a_dict = {
                        "words": a.get_text(),
                        "wikiUrl": a.get("href"),

                    }
                    a_dict.update(kwargs)
                    words.append(a_dict)
                nyms_list.append((related_index, words, relation_type))

        return nyms_list
    
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

    def grab_from_url(self, url, old_id=None, lang=None, include_dialects=True):
        if lang is None:
            lang = self.language
        response = self.session.get(url, params={'oldid': old_id})
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.clean_html()

        return self.get_word_data(lang.lower(), include_dialects=include_dialects)
    
    def deorphanize(self, wikiUrl, language, **kwargs):
        url = self.__base_url + wikiUrl
        res = self.grab_from_url(url, lang=language, include_dialects=False)
        for i in range(len(res)):
            res[i]['word'] = kwargs.get('word')
            res[i]['query'] = kwargs.get('query')
        return res

    def fetch(self, word, language=None, old_id=None, query=None, include_dialects=True):
        language = self.language if not language else language
        languages = language if hasattr(language, '__iter__') and type(language) != str else [language]
        self.current_url = self.url.format(word, self.use_printable)
        self.current_word = word
        res = []

        for lang in languages:
            res += self.grab_from_url(self.current_url, old_id=old_id, lang=lang, include_dialects=include_dialects)

        for i in range(len(res)):
            res[i]['query'] = res[i].get('query', word) if query is None else query
            res[i]['word'] = res[i].get('word', word)

        return res
        

    def fetch_all_potential(self, word, query=None, language=None, old_id=None, verbose=0, include_dialects=True):
        def get_possible_altenrnatives(word):
            replacement_dict = {
                "ا": ["ا", "أ", "إ", "آ"],
                " ": "_"
            }
            replacement_dict = {k: f"({'|'.join(v)})" for k, v in replacement_dict.items()}

            trans = str.maketrans(replacement_dict)
            word_regex = word.translate(trans)

            return list(exrex.generate(word_regex))
        
        possible_altenrnatives = get_possible_altenrnatives(word)
        res = {word: self.fetch(word, query=word, include_dialects=include_dialects)}
        if query is None:
            query = word
        if verbose > 0:
            possible_altenrnatives = tqdm.tqdm(possible_altenrnatives, desc="Fetching potential forms", leave=False)
        for w in possible_altenrnatives:
            if verbose > 0:
                possible_altenrnatives.set_postfix(w)

            fetch_res = self.fetch(w, language=language, old_id=old_id, query=query)
            if fetch_res:
                res[w] = fetch_res
        return res