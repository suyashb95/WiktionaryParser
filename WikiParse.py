import re,requests
import html2text
from utils import data,definition,relatedWord
from string import digits

response = requests.get('https://en.wiktionary.org/w/index.php?title=test&printable=yes')

partsOfSpeech = ["noun","verb","adjective","adverb","determiner",
				"article","preposition","conjunction","proper noun","letter",
				"character","phrase","proverb","idiom","symbol","syllable"]
		
relations = ["synonyms","antonyms","hypernyms","hyponyms",
			"meronyms","holonyms","troponyms","related terms","derived terms","coordinate terms"]
			
unwantedList = ['English','Pronunciation','External links','Anagrams','References','Statistics','See also']
			
def getIDList(contents,contentType):
	'''
	Returns a list of IDs relating to the specific content type.
	Text can be obtained by parsing the text within span tags having those IDs.
	'''
	if contentType == 'etymologies':
		checkList = ['etymology']
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
			IDList.append((contentIndex,contentID,textToCheck))
	return IDList
				
def getWordData(soup):
	contents = contents = soup.findAll('span',{'class':'toctext'})
	englishContents = []
	if contents[0].text == 'English':
		for content in contents:
			index =  content.find_previous().text.split('.')
			if index[0] == '1':
				englishContents.append(content)
	wordContents = []
	for content in englishContents:
		if content.text not in unwantedList:
			wordContents.append(content)
	etymologyIDs = getIDList(wordContents,'etymologies')
	definitionIDs = getIDList(wordContents,'definitions')
	relatedIDs = getIDList(wordContents,'related')
	#print etymologyIDs,definitionIDs,relatedIDs
	etymologyList, definitionList, examplesList, relatedWordsList = parseData(soup,etymologyIDs,definitionIDs,relatedIDs)
	JSONObjList = makeClass(etymologyList, definitionList, examplesList, relatedWordsList)
	return JSONObjList
	
def parseData(soup, etymologyIDs = None, definitionIDs = None, relatedIDs = None):
	'''
	Parses data from the soup using IDs returned by getIDList
	returns 4 lists, etymologies, definitions, examples and related words.
	'''
	etymologyList = []
	definitionList = []
	examplesList = []
	relatedWordsList = []
	htmlParser = html2text.HTML2Text()
	htmlParser.ignore_links = True
	for etymologyIndex, etymologyID, _ in etymologyIDs:
		spanTag = soup.findAll('span',{'id':etymologyID})[0]
		etymologyText = htmlParser.handle(spanTag.parent.findNextSibling().text)
		etymologyList.append((etymologyIndex,etymologyText))
	for definitionIndex, definitionID, definitionType in definitionIDs:
		spanTag = soup.findAll('span',{'id':definitionID})[0]
		table = spanTag.parent.findNextSibling().findNextSibling()
		for element in table.findAll('ul'):
			element.clear()
		for element in table.findAll('dd'):
			if not (element.text.startswith('(') and element.text.endswith(')')):
				examplesList.append((element.text,definitionType))
			element.clear()
		definitionText = htmlParser.handle(spanTag.parent.findNextSibling().text)
		for element in table.findAll('li'):
			definitionText += element.text
		definitionList.append((definitionIndex, definitionText, definitionType))
	'''
	print etymologyList
	print '\n\n'
	print definitionList
	print "\n\n"
	print examplesList
	'''
	return etymologyList, definitionList, examplesList, relatedWordsList
		
def makeClass(etymologyList, definitionList, examplesList, relatedWordsList):
	'''
	Takes lists of etymologies, definitions, examples and relatedwords 
	and makes classes.
	'''
	JSONObjList = []
	if len(etymologyList) == 1:
		dataObj = data()
		dataObj.etymology = etymologyList[0][1]
		if len(definitionList) == 1:
			defObj = definition()
			defObj.text = definitionList[0][1]
			defObj.partOfSpeech = definitionList[0][2]
			dataObj.definitionList.append(defObj)
		else:
			for definitionIndex, definitionText, definitionType in definitonList:
				defObj = definition()
				defObj.text = definitionText
				defObj.partOfSpeech = definitionType
				dataObj.definitionList.append(defObj)
		JSONObjList.append(dataObj.to_json())
	else:
		for etymologyIndex, etymologyText in etymologyList:
			dataObj = data()
			for definitionIndex, definitionText, definitionType in definitionList:
				if etymologyIndex in definitionIndex:
					defObj = definition()
					defObj.text = definitionText
					defObj.partOfSpeech = definitionType
					dataObj.definitionList.append(defObj)
			JSONObjList.append(dataObj.to_json())
	return JSONObjList				
		
		
			
		
			
						
						
				
		
	
		
		
		
		
	