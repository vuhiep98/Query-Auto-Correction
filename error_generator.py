import random, re, json
import pandas as pd

from corrector.ultis import encode_numbers, decode_numbers

class ErrorGenrator:
	def __init__(self, error_rate=0.05):
		self.error_generator_model_dir = 'model/error_generator/'
		self.qwerty_error_dir = 'model/error_generator/'
		self.key2char, self.char2key = self._get_keyboard_character_transfer(self.error_generator_model_dir + 'keyboard_character_transfer.txt')
		self.keyboard_typing_dict = self._get_keyboard_typing_error_dict(self.qwerty_error_dir + 'keyboard_typing_error_dict.txt')
		self.error_rate = error_rate
	
	def _get_keyboard_character_transfer(self, dir):
		key_char = {}
		char_key = {}
		with open(dir, 'r', encoding='utf-8') as reader:
			for line in reader.readlines():
				char, key = line.replace('\n', '').split('-')
				key_char[key] = char
				char_key[char] = key
		return key_char, char_key
	
	def _get_keyboard_typing_error_dict(self, qwerty_error_dir):
		return json.loads(open(qwerty_error_dir, 'r', encoding='utf-8').read())

	def _duplicate_typing(self, key):
		if key!='space':
			return key + '+' + key
		else:
			return key
	
	def _miss_typing(self, key):
		return ''
	
	def _wrong_typing(self, key):
		return random.choice(self.keyboard_typing_dict.get(key, [key]))

	def _text2key(self, text):
		return '+'.join([self.char2key.get(character, character) for character in text])
	
	def _key2text(self, key_chain):
		key_chain = re.sub('space', ' ', key_chain)
		for key, value in self.key2char.items():
			if key!='space' and len(key)==5:
				key_chain = re.sub(re.escape(key), value, key_chain)
		for key, value in self.key2char.items():
			if key!='space' and len(key)==3:
				key_chain = re.sub(re.escape(key), value, key_chain)
		return ''.join(key_chain.split('+'))
	
	def _generate_typing_error(self, key_chain):
		keys = key_chain.split('+')
		error_num = int(self.error_rate*keys.count('space')) + 1
		for _ in range(error_num):
			error_index = random.choice(range(0, len(keys)))
			while keys[error_index] == '#':
				error_index = random.choice(range(0, len(keys)))
			error_type = random.choice([1, 2, 3])
			if error_type == 1:
				keys[error_index] = self._duplicate_typing(keys[error_index])
			elif error_type == 2:
				keys[error_index] = self._miss_typing(keys[error_index])
			else:
				keys[error_index] = self._wrong_typing(keys[error_index])
		return '+'.join(keys), error_num
	
	def _encode_num(self, text):
		numbers = re.findall('[\S]*\d+[\S]*', text)
		return re.sub('[\S]*\d+[\S]*', '#', text), numbers
	
	def _decode_num(self, text, numbers):
		tokens = text.split(' ')
		last_index = 0
		for num in numbers:
			try:
				index = tokens.index('#', last_index)
			except ValueError:
				index = -1
			if index:
				tokens[index] = num
				last_index = index
		return ' '.join(tokens)
	
	def test_encode(self, text):
		print(text)
		text, numbers = self._encode_num(text)
		print(text)
		key_chain = self._text2key(text)
		print(key_chain)
		text = self._key2text(key_chain)
		print(text)
		text = self._decode_num(text, numbers)
		print(text)
		
	def error(self, text):
		text, numbers = self._encode_num(text)
		key_chain = self._text2key(text)
		# print(key_chain)
		key_chain, error_num = self._generate_typing_error(key_chain)
		# print(key_chain)
		text = self._key2text(key_chain)
		text = self._decode_num(text, numbers)
		return [text, error_num]


if __name__ == '__main__':
	error_generator = ErrorGenrator(error_rate=0.2)
	# error_generator.test_encode('thông tư số va/đtad-221 ngày 22 tháng 1 năm 2016')

	correct_queries = [line.replace('\n', '') for line in open('testing_input.txt', 'r', encoding='utf-8').readlines()]
	error_queries = [error_generator.error(query) for query in correct_queries]

	pd.DataFrame([[query[0], correct, query[1]] for query, correct in zip(error_queries, correct_queries)], 
				 columns=['query', 'correct', 'number of errors']).to_csv('testing_file.csv', index=False)
