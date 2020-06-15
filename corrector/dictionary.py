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
		threshold = 1
		
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
	
	
	@classmethod
	def load_dict(cls):
		cls.uni_dict, cls.n_uni, cls.uni_vocab_size = cls._from_text(file_name="unigrams")
		cls.bi_dict, cls.n_bi, cls.bi_vocab_size = cls._from_text(file_name="bigrams")
		# cls.tri_dict, cls.n_tri = cls._from_text(file_name="trigrams")
		cls._lambda = 0.85
		cls._k = 1.
	
	@classmethod
	def load_context_dict(cls):
		print('Context dictionary...')
		with open(context_dict_dir, "r", encoding="utf-8") as reader:
			try:
				cls.context_dict = json.load(reader)
			except FileNotFoundError:
				print("Context dictionary does not exist")

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
	def cpw(self, cur, prev):
		return float(self._c2w(prev + '_' + cur) + self._k)/\
				(self._c1w(prev) + self._k*self.uni_vocab_size)

	@memo
	def interpolation_cpw(self, cur, prev):
		return self._lambda*self.cpw(cur, prev) + (1. - self._lambda)*self.pw(prev)

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
