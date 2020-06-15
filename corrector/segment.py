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
		return [[text[:i], text[i:]] for i in range(1, len(text)) if lambda x: '_'.join(x) in self.bi_dict]

	def segment_token(self, text):
		if not text:
			return []
		best_candidate = max(self._split(text), key=lambda x: self._c2w('_'.join(x)))
		return best_candidate
		
	def segment(self, text):
		tokens = text.split()
		segmented_tokens = []
		for token in tokens:
			if token not in self.uni_dict:
				best_segment_cadidate = self.segment_token(token)
				if best_segment_cadidate:
					segmented_tokens += best_segment_cadidate
					continue
			segmented_tokens.append(token)

		return ' '.join(segmented_tokens)