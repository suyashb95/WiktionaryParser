from json import JSONEncoder


class data(object):
	
	def __init__(self,etymology = None,definitions = None):
		self.etymology = etymology
		self.definitions = definitions
		
		@property
		def definitions(self):
			return self._definitions 
		
		@definitions.setter
		def definitions(self,definitions):
			if definitions is None:
				self._definitions = []
				return
			if not isinstance(definitions,list):
				raise TypeError('Invalid type for relatedWord')
			for element in definitions:
				if not isinstance(element,definition):
					raise TypeError('Invalid type for relatedWord')
			else:
				self._definitions = definitions
				
		def to_json(self):
			return {'etymology': self.etymology if self.etymology else '',
					'definitions': [definition.to_json() for definition in self.definitions] if self.definitions else []}
			
class definition(object):
	
	def __init__(self,partOfSpeech = None,text = None,relatedWords = None):
		self.partOfSpeech = partOfSpeech
		self.text = text
		self.relatedWords = relatedWords

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
				'text': self._text if self.text else '',
				'relatedWords': [relatedWord.to_json() for relatedWord in self.relatedWords] if self.relatedWords else []
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