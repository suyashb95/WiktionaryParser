from json import JSONEncoder


class data(object):
	
	def __init__(self,etymology = None,definitions = None):
		self.etymology = etymology
		self.definitionList = definitions

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
		return {'etymology': self.etymology if self.etymology else '',
				'definitions': [definition.to_json() for definition in self.definitionList] if self.definitionList else [],
				}
			
class definition(object):
	
	def __init__(self,partOfSpeech = None,text = None,relatedWords = None, exampleUses = None):
		self.partOfSpeech = partOfSpeech
		self.text = text
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
		for element in relatedWords:
			if not isinstance(element,relatedWord):
				raise TypeError('Invalid type for relatedWord')
		else:
			self._relatedWords = relatedWords
			
	def to_json(self):
		return {'partOfSpeech': self.partOfSpeech if self.partOfSpeech else '',
				'text': self.text if self.text else '',
				'relatedWords': [relatedWord.to_json() for relatedWord in self.relatedWords] if self.relatedWords else [],
				'exampleUses': self.exampleUses if self.exampleUses else []
				}
		
class relatedWord(object):
	
	def __init__(self,relationshipType = None,words = None):
		self.relationshipType = relationshipType
		self.words = words
	
	@property
	def words(self):
		return self._words
		
	@words.setter
	def words(self,words):
		if words is None:
			self._words = []
			return
		if isinstance(words,list):
			self._words = words
		else:
			raise TypeError('Invalid type for words')
			
	def to_json(self):
		return {'relationshipType': self.relationshipType if self.relationshipType else '',
				'words': self.words if self.words else []
				}