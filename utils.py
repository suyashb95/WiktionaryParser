from json import JSONEncoder


class WordData(object):
	
	def __init__(self,etymology = None,definitions = None, pronunciations = None, audioLinks = None):
		self.etymology = etymology if etymology else ''
		self.definition_list = definitions
		self.pronunciations = pronunciations if pronunciations else []
		self.audio_links = audioLinks if audioLinks else []
	
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
	def definition_list(self):
		return self._definition_list
			
	@definition_list.setter
	def definition_list(self,definitions):
		if definitions is None:
			self._definition_list = []
			return
		elif not isinstance(definitions,list):
			raise TypeError('Invalid type for definition')
		for element in definitions:
			if not isinstance(element,definition):
				raise TypeError('Invalid type for definition')
		else:
			self._definition_list = definitions
			
	def toJSON(self):
		return {'etymology': self.etymology,
				'definitions': [definition.toJSON() for definition in self._definition_list],
				'pronunciations': self.pronunciations,
				'audioLinks': self.audio_links
				}
			
class Definition(object):
	
	def __init__(self,part_of_speech = None,text = None,related_words = None, example_uses = None):
		self.part_of_speech = part_of_speech if part_of_speech else ''
		self.text = text if text else ''
		self.related_words = related_words
		self.example_uses = example_uses
	
	@property
	def example_uses(self):
		return self._example_uses
		
	@example_uses.setter
	def example_uses(self, example_uses):
		if example_uses is None:
			self._example_uses = []
			return
		elif not isinstance(example_uses,list):
			raise TypeError('Invalid type for examle_uses')
		else:
			for example in example_uses:
				if not isinstance(example,str):
					raise TypeError('Invalid type for examle_uses')
					return
			self._example_uses = example_uses
			
	@property
	def related_words(self):
		return self._related_words
			
	@related_words.setter
	def related_words(self,related_words):
		if related_words is None:
			self._related_words = []
			return
		elif not isinstance(related_words,list):
			raise TypeError('Invalid type for relatedWord')
		else:
			for element in related_words:
				if not isinstance(element,RelatedWord):
					raise TypeError('Invalid type for relatedWord')
					return
			self._related_words = related_words
			
	def toJSON(self):
		return {'partOfSpeech': self.part_of_speech if self.part_of_speech else '',
				'text': self.text if self.text else '',
				'relatedWords': [related_word.toJSON() for related_word in self.related_words] if self.related_words else [],
				'exampleUses': self.example_uses if self.example_uses else []
				}
		
class RelatedWord(object):
	
	def __init__(self,relationship_type = None,words = None):
		self.relationship_type = relationship_type if relationship_type else ''
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

			
	def toJSON(self):
		return {'relationshipType': self.relationship_type if self.relationship_type else '',
				'words': self.words if self.words else []
				}