from json import JSONEncoder


class WordData(object):
	
	def __init__(self,etymology = None,definitions = None, pronunciations = None, audioLinks = None):
		self.etymology = etymology if etymology else ''
		self.definitionList = definitions
		self.pronunciations = pronunciations if pronunciations else []
		self.audioLinks = audioLinks if audioLinks else []
	
	'''	
	@property 
	def etymology(self):
		return self._etymology
		
	@etymology.setter
	def etymology(self, etymology):
		if etymology is None:
			etymology = ''
			return
		elif not isinstance(etymology,str):
			raise TypeError('Invalid type for etymology')
		else:
			self._etymology = etymology
	'''
			
	@property
	def definitionList(self):
		return self._definitionList
			
	@definitionList.setter
	def definitionList(self,definitions):
		if definitions is None:
			self._definitionList = []
			return
		elif not isinstance(definitions,list):
			raise TypeError('Invalid type for definition')
		for element in definitions:
			if not isinstance(element,definition):
				raise TypeError('Invalid type for definition')
		else:
			self._definitionList = definitions
			
	def to_json(self):
		return {'etymology': self.etymology,
				'definitions': [definition.to_json() for definition in self.definitionList],
				'pronunciations': self.pronunciations,
				'audioLinks': self.audioLinks
				}
			
class Definition(object):
	
	def __init__(self,partOfSpeech = None,text = None,relatedWords = None, exampleUses = None):
		self.partOfSpeech = partOfSpeech if partOfSpeech else ''
		self.text = text if text else ''
		self.relatedWords = relatedWords
		self.exampleUses = exampleUses
	
	@property
	def exampleUses(self):
		return self._exampleUses
		
	@exampleUses.setter
	def exampleUses(self, exampleUses):
		if exampleUses is None:
			self._exampleUses = []
			return
		elif not isinstance(exampleUses,list):
			raise TypeError('Invalid type for exampleUses')
		else:
			for example in exampleUses:
				if not isinstance(example,str):
					raise TypeError('Invalid type for exampleUses')
					return
			self._exampleUses = exampleUses
			
	@property
	def relatedWords(self):
		return self._relatedWords
			
	@relatedWords.setter
	def relatedWords(self,relatedWords):
		if relatedWords is None:
			self._relatedWords = []
			return
		elif not isinstance(relatedWords,list):
			raise TypeError('Invalid type for relatedWord')
		else:
			for element in relatedWords:
				if not isinstance(element,RelatedWord):
					raise TypeError('Invalid type for relatedWord')
					return
			self._relatedWords = relatedWords
			
	def to_json(self):
		return {'partOfSpeech': self.partOfSpeech if self.partOfSpeech else '',
				'text': self.text if self.text else '',
				'relatedWords': [relatedWord.to_json() for relatedWord in self.relatedWords] if self.relatedWords else [],
				'exampleUses': self.exampleUses if self.exampleUses else []
				}
		
class RelatedWord(object):
	
	def __init__(self,relationshipType = None,words = None):
		self.relationshipType = relationshipType if relationshipType else ''
		self.words = words
	
	@property
	def words(self):
		return self._words
		
	@words.setter
	def words(self,words):
		if words is None:
			self._words = []
			return
		if not isinstance(words,list):
			raise TypeError('Invalid type for words')
		else:
			for word in words:
				if not isinstance(word,str):
					raise TypeError('Invalid type for words.')
					return
			self._words = words

			
	def to_json(self):
		return {'relationshipType': self.relationshipType if self.relationshipType else '',
				'words': self.words if self.words else []
				}