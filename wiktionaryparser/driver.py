import argparse

from wiktionaryparser import WiktionaryParser


def wiktionary_lookup(word,language="english"):
    parser = WiktionaryParser()
    parser.set_default_language(language)
    result = parser.fetch(word)
    if len(result) == 0:
        return ["*** WiktionaryParser didn't find anything"]
    else:
        if "additional_info" in result[0]:
            return [result[0]["additional_info"]]
        else:
            if "definitions" in result[0] and len(result[0]["definitions"]) > 0:
                return [definition for definition in result[0]["definitions"][0]["text"]]
            else:
                return ["** WiktionaryParser didn't find any definitions"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check <word> against Wiktionary using WiktionaryParser")
    parser.add_argument("-m", "--multiple-languages", action="store_true",
                        help="if present, look up <word> for several languages; otherwise, just English")

    parser.add_argument("word", help="the word to look up")
    args = parser.parse_args()

    if args.multiple_languages:
        languages = ["english", "french", "italian", "japanese"]
    else:
        languages = ["english"]

    for language in languages:
        if args.multiple_languages:
            print("\n----------------------------------------")
            print(f"Trying {args.word} for {language = }")
        definitions = wiktionary_lookup(args.word, language)

        if len(definitions) > 0:
            for elem in definitions:
                print("-- ", elem[:80])
        if args.multiple_languages:
            print("----------------------------------------")

