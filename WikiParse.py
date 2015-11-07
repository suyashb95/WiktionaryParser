import re,requests
import html2text
from utils import WordData,Definition,RelatedWord
from string import digits
import re
from bs4 import BeautifulSoup as BS

partsOfSpeech = ["noun", "verb", "adjective", "adverb", "determiner",
                "article", "preposition", "conjunction", "proper noun",
                "letter", "character", "phrase", "proverb", "idiom",
                "symbol", "syllable", "numeral",  "initialism"]

relations = ["synonyms", "antonyms", "hypernyms", "hyponyms",
            "meronyms", "holonyms", "troponyms", "related terms",
            "derived terms", "coordinate terms"]

unwantedList = ['English','External links',
                'Anagrams', 'References',
                'Statistics','See also']


def getIDList(contents, contentType):
    '''
    Returns a list of IDs relating to the specific content type.
    Text can be obtained by parsing the text within span tags having those IDs.
    '''
    if contentType == 'etymologies':
        checkList = ['etymology']
    elif contentType == 'pronunciation':
        checkList = ['pronunciation']
    elif contentType =='definitions':
        checkList = partsOfSpeech
    elif contentType == 'related':
        checkList = relations
    else:
        return None
    IDList = []
    for contentTag in contents:
        contentIndex = contentTag.find_previous().text
        textToCheck = ''.join([i for i in contentTag.text if not i.isdigit()]).strip().lower()
        if textToCheck in checkList:
            contentID = contentTag.parent['href'].replace('#','')
            IDList.append((contentIndex, contentID, textToCheck))
    return IDList

def getWordData(soup, language):
    '''
    Hardcoded to get Enlglish content.
    Have to change later.
    Match language, get previous tag, get starting number.
    '''
    contents = soup.findAll('span',{'class':'toctext'})
    languageContents = []
    startIndex = None
    for content in contents:
        if content.text.lower() == language:
            startIndex = content.find_previous().text + '.'
    if startIndex is None:
        return []
    for content in contents:
        index =  content.find_previous().text
        if index.startswith(startIndex):
            languageContents.append(content)
    wordContents = []
    for content in languageContents:
        if content.text not in unwantedList:
            wordContents.append(content)

    '''
    Get IDs for etymology, definitions, examples and related words.
    '''

    etymologyIDs = getIDList(wordContents,'etymologies')
    definitionIDs = getIDList(wordContents,'definitions')
    relatedIDs = getIDList(wordContents,'related')
    pronunciationIDs = getIDList(wordContents,'pronunciation')
    '''
    Parse text from those tags.
    Must call parseExamples before parseDefinitions.
    '''
    etymologyList = parseEtymologies(soup, etymologyIDs)
    examplesList = parseExamples(soup, definitionIDs)
    definitionsList = parseDefinitions(soup, definitionIDs)
    relatedWordsList = parseRelatedWords(soup, relatedIDs)
    pronunciationList = parsePronunciations(soup, pronunciationIDs)
    
    JSONObjList = makeClass(etymologyList, 
                            definitionsList, 
                            examplesList, 
                            relatedWordsList,
                            pronunciationList)
    return JSONObjList

def parsePronunciations(soup, pronunciationIDs = None):
    pronunciationList = []
    for pronunciationIndex, pronunciationID, _ in pronunciationIDs:
        spanTag = soup.findAll('span', {'id':pronunciationID})[0]
        listTag = spanTag.parent
        while listTag.name != 'ul':
            listTag = listTag.findNextSibling()
        for supTag in listTag.findAll('sup'):
            supTag.clear()
        audioLinks = []
        pronunciationText = []
        for listElement in listTag.findAll('li'):
            for audioTag in listElement.findAll('div', {'class':'mediaContainer'}):
                audioLinks.append(audioTag.find('source')['src'])
                listElement.clear()
            if(listElement.text):
                pronunciationText.append(listElement.text.encode('utf-8'))
        pronunciationList.append((pronunciationIndex, pronunciationText, audioLinks))
    return pronunciationList
    
def parseDefinitions(soup, definitionIDs = None):
    definitionsList = []
    for definitionIndex, definitionID, definitionType in definitionIDs:
        spanTag = soup.findAll('span',{'id':definitionID})[0]
        table = spanTag.parent
        definitionTag = None
        '''
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses and all.
        '''
        while table.name != 'ol':
            definitionTag = table
            table = table.findNextSibling()
        definitionText = (definitionTag.text) + '\n'
        for element in table.findAll('li'):
            definitionText += element.text
        definitionText = re.sub('(\\n+)', '\\n', definitionText).strip()
        definitionsList.append((definitionIndex, definitionText.encode('utf-8'), definitionType))
    return definitionsList

def parseExamples(soup, definitionIDs = None):
    examplesList = []
    for definitionIndex, definitionID, definitionType in definitionIDs:
        spanTag = soup.findAll('span', {'id':definitionID})[0]
        table = spanTag.parent
        definitionTag = None
        '''
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses and all.
        '''
        while table.name != 'ol':
            definitionTag = table
            table = table.findNextSibling()
        '''
        <ul> tags have biblical references and quotes.
        Removing them for now.
        '''
        for element in table.findAll('ul'):
            element.clear()
        '''
        <dd> tags have examples, take them and clear.
        '''
        examples = []
        for element in table.findAll('dd'):
            exampleText = element.text.strip()
            if exampleText and not (exampleText.startswith('(') and exampleText.endswith(')')):
                examples.append(exampleText.encode('utf-8'))
            element.clear()
        examplesList.append((definitionIndex, examples, definitionType))
    return examplesList

def parseEtymologies(soup, etymologyIDs = None):
    etymologyList = []
    for etymologyIndex, etymologyID, _ in etymologyIDs:
        spanTag = soup.findAll('span', {'id':etymologyID})[0]
        etymologyTag = spanTag.parent
        '''
        Word etymology is either a para or a list.
        move forward till you find either.
        '''
        while etymologyTag.name not in ['p', 'ul']:
            etymologyTag = etymologyTag.findNextSibling()
        if etymologyTag.name == 'p':
            etymologyText = (etymologyTag.text)
        else:
            etymologyText = ''
            for listTag in etymologyTag.findAll('li'):
                etymologyText += (listTag.text)
        etymologyList.append((etymologyIndex, etymologyText.encode('utf-8')))
    return etymologyList

def parseRelatedWords(soup, relatedIDs = None):
    relatedWordsList = []
    '''
    Look for parent tags with <li> tags, those are related words.
    <li> tags can either be in tables or lists.
    '''
    for relatedIndex, relatedID, relationType in relatedIDs:
        words = []
        spanTag = soup.findAll('span', {'id':relatedID})[0]
        parentTag = spanTag.parent
        while not parentTag.findAll('li'):
            parentTag = parentTag.findNextSibling()
        for listTag in parentTag.findAll('li'):
            words.append(listTag.text.encode('utf-8'))
        relatedWordsList.append((relatedIndex, words, relationType))
    return relatedWordsList

def makeClass(etymologyList, 
                definitionsList,
                examplesList, 
                relatedWordsList,
                pronunciationList):
    JSONObjList = []
    for etymologyIndex, etymologyText in etymologyList:
        dataObj = WordData()
        dataObj.etymology = etymologyText
        for pronunciationIndex, pronunciations, audioLinks in pronunciationList:
            if pronunciationIndex.startswith(etymologyIndex) or pronunciationIndex.count('.') == 1:
                dataObj.pronunciations = pronunciations
                dataObj.audioLinks = audioLinks
        for definitionIndex, definitionText, definitionType in definitionsList:
            if definitionIndex.startswith(etymologyIndex) or definitionIndex.count('.') == 1:
                defObj = Definition()
                defObj.text = definitionText
                defObj.partOfSpeech = definitionType
                for exampleIndex, examples, exampleType in examplesList:
                    if exampleIndex.startswith(definitionIndex):
                        defObj.exampleUses = examples
                for relatedWordIndex, relatedWords, relationType in relatedWordsList:
                    if relatedWordIndex.startswith(definitionIndex) or relatedWordIndex.count('.') == 2:
                        relatedWordObj = RelatedWord()
                        relatedWordObj.words = relatedWords
                        relatedWordObj.relationshipType = relationType
                        defObj.relatedWords.append(relatedWordObj)
                dataObj.definitionList.append(defObj)
        JSONObjList.append(dataObj.to_json())
    return JSONObjList

def main():
    word = raw_input('Enter word: ')
    language = raw_input('Enter language: ')
    base_url = 'https://en.wiktionary.org/wiki/'
    response = requests.get(base_url + word + '?printable=yes')
    soup = BS(response.text, 'html.parser')
    return getWordData(soup, language.lower())