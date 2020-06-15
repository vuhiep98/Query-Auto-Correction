import sys
from os.path import dirname, realpath
from math import log, log10
from tqdm import tqdm
import json
from symspellpy.symspellpy import SymSpell
from textdistance import levenshtein, jaro_winkler
import numpy as np

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from corrector.ultis import product, memo


model_dir="models/"
diacritic_adder="models/diacritic_adder.txt"
context_dict_dir="models/context_dict.txt"


class Dictionary:

	def __init__(self):
		# self.verbosity = Verbosity.ALL
		pass
	
	@classmethod
	def _from_text(cls, file_name="unigrams"):
		dct = {}
		n = 0
		vocab_size = 0
		threshold = 2
		
		with open(model_dir + file_name + ".txt", "r", encoding="utf-8") as reader:
			for line in tqdm(reader.readlines(), desc=file_name):
				line = line.replace("\n", "")
				key, value = line.split()
				value = int(value)
				if value >= threshold:
					dct[key] = value
					n += value
					vocab_size += 1
		return dct, n, vocab_size
	
	
	# @classmethod
	# def load_symspell(cls):
	# 	print('Symspell object...')
	# 	cls.symspell = SymSpell(max_dictionary_edit_distance=3)
	# 	cls.symspell.load_dictionary(
	# 		"model/new_content/unigrams.txt",
	# 		term_index=0,
	# 		count_index=1,
	# 		separator=" ",
	# 		encoding="utf-8"
	# 	)
	
	@classmethod
	def load_dict(cls):
		cls.uni_dict, cls.n_uni, cls.uni_vocab_size = cls._from_text(file_name="unigrams")
		cls.bi_dict, cls.n_bi, cls.bi_vocab_size = cls._from_text(file_name="bigrams")
		# cls.tri_dict, cls.n_tri = cls._from_text(file_name="trigrams")
		cls._d = 0.75
	
	@classmethod
	def load_context_dict(cls):
		print('Context dictionary...')
		with open(context_dict_dir, "r", encoding="utf-8") as reader:
			try:
				cls.context_dict = json.load(reader)
			except FileNotFoundError:
				print("Context dictionary does not exist")

	@classmethod
	def create_cont_dict(cls):
		cls.cont_dict_2 = {}
		for bi, freq in tqdm(cls.bi_dict.items(), desc='Bigram contianuation'):
			tokens = bi.split('_')

			if tokens[0] not in cls.cont_dict_2:
				cls.cont_dict_2[tokens[0]] = {
					'before': freq,
					'after': 0,
					'before_num': 1,
					'after_num': 0
				}
			else:
				cls.cont_dict_2[tokens[0]]['before'] += freq
				cls.cont_dict_2[tokens[0]]['before_num'] += 1

			if tokens[1] not in cls.cont_dict_2:
				cls.cont_dict_2[tokens[1]] = {
					'before': 0,
					'after': freq,
					'before_num': 0,
					'after_num': 1
				}
			else:
				cls.cont_dict_2[tokens[1]]['after'] += freq
				cls.cont_dict_2[tokens[1]]['after_num'] += 1

		# cls.cont_dict_3 = {}
		# for tri, freq in tqdm(cls.tri_dict.items(), desc='Trigram contianuation'):
		# 	tokens = tri.split('_')
		# 	phrase = tokens[0] + ' ' + tokens[1]

		# 	if phrase not in cls.cont_dict_3:
		# 		cls.cont_dict_3[phrase] = freq
		# 	else:
		# 		cls.cont_dict_3[phrase] += freq

		# 	if tokens[2] not in cls.cont_dict_3:
		# 		cls.cont_dict_3[tokens[2]] = freq
		# 	else:
		# 		cls.cont_dict_3[tokens[2]] += freq

	@classmethod
	def load_diacritic_adder(cls):
		print('Diacritic adder...')
		cls.diacritic = []
		with open(diacritic_adder, "r", encoding="utf-8") as reader:
			line = reader.readline()
			while line:
				cls.diacritic.append([c for c in line.replace('\n', '')])
				line = reader.readline()
	
	def _c1w(self, word):
		return self.uni_dict.get(word, 0)

	def _c2w(self, phrase):
		return self.bi_dict.get(phrase, 0)
	
	def _c3w(self, phrase):
		return self.tri_dict.get(phrase, 0)

	def pw(self, word):
		return float(self._c1w(word))/self.n_uni

	@memo
	def _lambda(self, prev, prev_prev=None):
		if prev_prev is None:
			try:
				return (self._d/self.cont_dict_2[prev]['before'])*self.cont_dict_2[prev]['before_num']
			except (ZeroDivisionError, KeyError):
				return 0
		else:
			phrase = prev_prev + '_' + prev
			try:
				return (self._d/self._c2w(phrase))*self.cont_dict_3[phrase]
			except (ZeroDivisionError, KeyError):
				return 0

	@memo
	def _p_cont(self, word):
		try:
			return float(self.cont_dict_2[word]['after_num'])/self.n_bi
		except KeyError:
			return 0

	@memo
	def cpw(self, cur, prev):
		try:
			first_term = float(max(self._c2w(prev + '_' +cur) - self._d, 0))/\
						self._c1w(prev)
		except ZeroDivisionError:
			first_term = 0

		kn_lambda = self._lambda(prev)
		p_cont = self._p_cont(cur)

		return first_term + kn_lambda*p_cont

	@memo
	def cp3w(self, cur, prev, prev_prev):
		try:
			first_term = float(max(self._c3w(prev_prev + '_' + prev + '_' + cur) - self._d, 0))/\
						self._c2w(prev_prev + '_' + prev)
		except ZeroDivisionError:
			first_term = 0

		kn_lambda = self._lambda(prev, prev_prev)
		p_cont = self.cpw(cur, prev)

		return first_term + kn_lambda*p_cont

	# @memo
	# def cp3w(self, cur, prev, prev_prev):
	# 	delta = self._delta_coeff(cur, prev, prev_prev)
	# 	prob = delta["1"]*self._p3w(cur, prev, prev_prev) + \
	# 		   delta["2"]*self.cpw(cur, prev) + \
	# 		   delta["3"]*self.pw(cur)
	# 	return prob

	def common_context(self, w_1, w_2):
		cont_1 = set(self.context_dict.get(w_1, []))
		cont_2 = set(self.context_dict.get(w_2, []))
		common = cont_1.intersection(cont_2)
		return len(common)

	def p_context(self, word, candidate):
		try:
			return float(self.common_context(word, candidate))/len(self.context_dict.get(word, []))
		except ZeroDivisionError:
			return 0.0

	def words_similarity(self, w1, w2):
		return 1/2*(levenshtein.normalized_similarity(w1, w2) +\
				jaro_winkler.normalized_similarity(w1, w2))

	def p_sentence(self, sentence):
		tokens = sentence.split()
		probs = [self.pw(token) for token in tokens]
		return np.prod(probs)
