import re,requests
import html2text
from utils import data,definition,relatedWord
from string import digits
import re

response = requests.get('https://en.wiktionary.org/w/index.php?title=test&printable=yes')

partsOfSpeech = ["noun","verb","adjective","adverb","determiner",
				"article","preposition","conjunction","proper noun","letter",
				"character","phrase","proverb","idiom","symbol","syllable","numeral"]
		
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
	'''
	Hardcoded to get Enlglish content.
	Have to change later.
	'''
	contents = soup.findAll('span',{'class':'toctext'})
	englishContents = []
	if contents[0].text == 'English':
		for content in contents:
			index =  content.find_previous().text
			if index.startswith('1.'):
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
		etymologyTag = spanTag.parent
		'''
		Word etymology is either a para or a list.
		move forward till you find either.
		'''
		while etymologyTag.name not in ['p','ul']:
			etymologyTag = etymologyTag.findNextSibling()
		if etymologyTag.name == 'p':
			etymologyText = htmlParser.handle(etymologyTag.text)
		else:
			etymologyText = ''
			for listTag in etymologyTag.findAll('li'):
				etymologyText += htmlParser.handle(listTag.text)
		etymologyList.append((etymologyIndex,etymologyText))
		
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
			if not (element.text.startswith('(') and element.text.endswith(')')):
				examples.append(element.text)
			element.clear()
		examplesList.append((definitionIndex, examples, definitionType))
		print examplesList
		'''
		Add related text from the tag right befor the <ol>
		and parse each <li> tag to get definitions.
		'''
		definitionText = htmlParser.handle(definitionTag.text)
		for element in table.findAll('li'):
			definitionText += element.text
		definitionText = re.sub('(\\n+)', '\\n', definitionText).strip()
		definitionList.append((definitionIndex, definitionText, definitionType))
		
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
			words.append(listTag.text)
		relatedWordsList.append((relatedIndex, words, relationType))
	
		
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
			defObj.exampleUses = examplesList[0][1]
			print examplesList
			for relatedIndex, relatedWords, relationType in relatedWordsList:
				relatedWordObj = relatedWord()
				relatedWordObj.relationshipType = relationType
				relatedWordObj.words = relatedWords
				defObj.relatedWords.append(relatedWordObj)
			dataObj.definitionList.append(defObj)
		else:
			for definitionIndex, definitionText, definitionType in definitonList:
				defObj = definition()
				defObj.text = definitionText
				defObj.partOfSpeech = definitionType
				for relatedIndex, relatedWords, relationType in relatedWordsList:
					if definitionIndex in relatedIndex:
						relatedWordObj = relatedWord()
						relatedWordObj.relationshipType = relationType
						relatedWordObj.words = relatedwords
						defObj.relatedWords.append(relatedWordObj)
				for exampleIndex, examples, definitionType in examplesList:
					if definitionIndex in exampleIndex:
						defObj.exampleUses.append(examples)
				dataObj.definitionList.append(defObj)
		JSONObjList.append(dataObj.to_json())
	else:
		for etymologyIndex, etymologyText in etymologyList:
			dataObj = data()
			dataObj.etymology = etymologyText
			if len(definitionList) == 1:
				defObj = definition()
				defObj.text = definitionList[0][1]
				defObj.partOfSpeech = definitionList[0][2]
				defObj.exampleUses = examplesList[0][1]
				for relatedIndex, relatedWords, relationType in relatedWordsList:
					relatedWordObj = relatedWord()
					relatedWordObj.relationshipType = relationType
					relatedWordObj.words = relatedwords
					defObj.relatedWords.append(relatedWordObj)
				dataObj.definitionList.append(defObj)
			else:
				for definitionIndex, definitionText, definitionType in definitionList:
					defObj = definition()
					defObj.text = definitionText
					defObj.partOfSpeech = definitionType
					for relatedIndex, relatedWords, relationType in relatedWordsList:
						if definitionIndex in relatedIndex:
							relatedWordObj = relatedWord()
							relatedWordObj.relationshipType = relationType
							relatedWordObj.words = relatedWords
							defObj.relatedWords.append(relatedWordObj)
					for exampleIndex, examples, definitionType in examplesList:
						if definitionIndex in exampleIndex:
							defObj.exampleUses.append(examples)
					dataObj.definitionList.append(defObj)
			JSONObjList.append(dataObj.to_json())
	return JSONObjList				
		
		
			
		
			
						
						
				
		
	
		
		
		
		
	