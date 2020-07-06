import sys
from os.path import dirname, realpath
from math import log10
from tqdm import tqdm
from symspellpy.symspellpy import Verbosity

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from corrector.ultis import memo, remove_diacritics
from corrector.dictionary import Dictionary

class Segmentor(Dictionary):

	def __init__(self):
		pass

	def _split(self, text):
		return [[text[:i+1], text[i+1:]] for i in range(0, min(10, len(text)))]

	def segment_token(self, text):
		if not text:
			return []
		candidates = [[first] + self.segment_token(remain) for first, remain in self._split(text)]
		return max(candidates, key=self.p_sentence)
		
	def segment(self, text):
		tokens = text.split()
		segmented_tokens = []
		for token in tokens:
			best_segment_cadidate = self.segment_token(token)
			if self.contain_bigram(best_segment_cadidate) and self.pw(token) < self.p_sentence(best_segment_cadidate): 
				segmented_tokens += best_segment_cadidate
			else:
				segmented_tokens += [token]
				
		return ' '.join(segmented_tokens)