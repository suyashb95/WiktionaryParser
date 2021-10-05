from wiktionaryparser.core import ContentParser


class ConjugationsParser(ContentParser):
    def parse_content(self, soup, language, word_contents):
        conjugation_id_list = self.get_id_list(soup, word_contents, ["conjugation"])
        conjugations_list = []
        for conjugation_index, conjugation_id, conjugation_type in conjugation_id_list:
            words = []
            span_tag = soup.find_all('span', {'id': conjugation_id})[0]
            parent_tag = span_tag.parent
            inflection_table = None
            while parent_tag and inflection_table is None:
                parent_tag = parent_tag.find_next_sibling()
                inflection_table = parent_tag.select_one('.inflection-table')

            if not inflection_table:
                return None

            conjugations = dict()
            infinitive_tag = inflection_table.find(lambda tag: tag.name == "b" and "Infinitive" in tag.text)
            if infinitive_tag:
                inf_container = infinitive_tag.select_one("strong")
                if inf_container:
                    conjugations["infinitive"] = inf_container.text

                conjugations["present"] = self.parse_inflection_row(inflection_table, "Present")
                conjugations["futur1"] = self.parse_inflection_row(inflection_table, "Future I")
                conjugations["futur2"] = self.parse_inflection_row(inflection_table, "Future II")
                conjugations["perfect"] = self.parse_inflection_row(inflection_table, "Perfect")
                conjugations["pluperfect"] = self.parse_inflection_row(inflection_table, "Pluperfect")
                conjugations["imperfect"] = self.parse_inflection_row(inflection_table, "Imperfect")
                conjugations["conditional1"] = self.parse_inflection_row(inflection_table, "Conditional I")
                conjugations["conditional2"] = self.parse_inflection_row(inflection_table, "Conditional II")
                conjugations["imperative"] = self.parse_inflection_row(inflection_table, "Imperative")

            conjugations_list.append((conjugation_index, conjugations))

        return conjugations_list

    def parse_inflection_row(self, inflection_table, row_name):
        inflection_tag = inflection_table.find(lambda tag: tag.name == "b" and row_name == tag.text)
        if not inflection_tag:
            return None

        inflection_form = inflection_tag.parent.find_next_sibling()
        inflection_forms = []
        while inflection_form:

            children = []
            child_forms = inflection_form.find_all("span", recursive=False)
            for child_form in child_forms:
                children.append(
                    " ".join([t.strip() for t in child_form.find_all(text=True) if len(t) > 0 and not t.isspace()]))

            if len(children) == 0:
                inflection_forms.append(None)
            elif len(children) == 1:
                inflection_forms.append(children[0])
            else:
                inflection_forms.append(children)

            inflection_form = inflection_form.find_next_sibling()

        return inflection_forms


class ConjugationsProcessor(object):
    def process_word_data(self, words, word_data):
        for word in words:
            for conjugation_index, conjugation in word_data['conjugation']:
                if word.contains_heading(conjugation_index):
                    word.data["conjugations"] = conjugation
