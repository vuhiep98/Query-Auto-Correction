import sys
from os.path import dirname, realpath
from math import log
from tqdm import tqdm
import re, json

from symspellpy.symspellpy import SymSpell, Verbosity

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from corrector.dictionary import Dictionary

class Corrector(Dictionary):

	def __init__(self):
		self.verbosity = Verbosity.ALL
		self.symspell = SymSpell(max_dictionary_edit_distance=3, count_threshold=0)
		self.spelling_error_threshold = 0.001

	def load_symspell(self):
		for k,v in tqdm(self.uni_dict.items(), 'Loading symspell...'):
			self.symspell.create_dictionary_entry(key=k, count=v)

	def _gen_character_candidates(self, character):
		for line in self.diacritic:
			if character in line:
				return line
		return [character]

	def _gen_word_candidates(self, word):
		cands = [word]
		for i in range(len(word)):
			can_list = self._gen_character_candidates(word[i])
			cands += [word[:i] + c + rest
						for c in can_list
						for rest in self._gen_word_candidates(word[i+1:])]
		return cands

	def _gen_diacritic_candidates(self, term):
		if term == '<num>':
			return [term]
		cands = list(set(self._gen_word_candidates(term)))
		cands = sorted(cands, key=lambda x: -self._c1w(x))[:min(10, len(cands))]
		return cands
	
	def _spell_checking(self, prev, cur, nex):
		prob = 0.
		if prev is None:
			prob = self.cpw(nex, cur)
		elif nex is None:
			prob = self.cpw(cur, prev)
		else:
			prob = self.cpw(cur, prev) * self.cpw(nex, cur)
		
		return prob >= self.spelling_error_threshold

	def gen_states(self, obs):
		states = {}
		new_obs = []

		if len(obs) == 0:
			return new_obs, states

		if len(obs) == 1:
			states[obs[0]] = [obs[0]]
			return obs, states
		
		for index, ob in enumerate(obs):
			states[ob] = []
			if len(ob)==1 and re.match(r"[^aáàảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoóòỏõọôồổỗộơờớởỡợuùúũụưứửữựyỳýỷỹỵ]", ob):
				continue

			new_obs += [ob]
			states[ob] = [ob]

			if index == 0:
				if self._spell_checking(prev=None, cur=ob, nex=obs[index+1]):
					continue
			elif index == len(obs)-1:
				if self._spell_checking(prev=obs[index-1], cur=ob, nex=None):
					continue
			elif self._spell_checking(obs[index-1], ob, obs[index+1]):
				continue

			if len(ob)<=4: edit_distance=1
			elif len(ob)>4 and len(ob)<=10: edit_distance=2
			elif len(ob)>10: edit_distance=3

			states[ob] += sorted([c.term for c in self.symspell.lookup(
				phrase=ob,
				verbosity=self.verbosity,
				max_edit_distance=edit_distance,
				include_unknown=False,
				ignore_token=r'<num>'
			)],
			key=lambda x: -self._c1w(x))[:20]
			# print('{0}: {1}'.format(ob, str(states[ob])))
		return new_obs, states
	
	def _trans(self, cur, prev):
		return self.interpolation_cpw(cur, prev)

	def _emiss(self, cur_observe, cur_state):
		return 1/2*(self.words_similarity(cur_observe, cur_state) +\
				self.pw(cur_state))

	def _viterbi_decoder(self, obs, states):
		V = [{}]
		path = {}

		for st in states[obs[0]]:
			V[0][st] = 1.0
			path[st] = [st]

		for i in range(1, len(obs)):
			V.append({})
			new_path = {}

			for st in states[obs[i]]:
				# if i==1:
				prob, state = max([
					(V[i-1][prev_st]*self._trans(st, prev_st)*self._emiss(obs[i], st), prev_st)
					for prev_st in states[obs[i-1]]
				])

				# else:
				# 	prob, state = max([
				# 		(V[i-1][prev_st]*self._trans(st, prev_st, prev_prev_st)*self._emiss(obs[i], st), prev_st)
				# 		for prev_st in states[obs[i-1]]
				# 		for prev_prev_st in states[obs[i-2]]
				# 	])

				V[i][st] = prob
				new_path[st] = path[state] + [st]

			path = new_path

		with open('data/viterbi_tracking.txt', 'w+', encoding='utf-8') as writer:
			# writer.write(json.dumps(path, indent=4, ensure_ascii=False) + '\n')
			writer.write(json.dumps(V, indent=4, ensure_ascii=False) + '\n')

		prob, state = max([(V[-1][st], st) for st in states[obs[-1]]])

		return {
			"prob": prob,
			"result": ' '.join(path[state])
		}

	def correct(self, text):
		# obs = ['<START>'] + text.split() + ['<END>']
		obs = text.split()
		obs, states = self.gen_states(obs)
		result = self._viterbi_decoder(obs, states)
		# return [" ".join(r[1:-1]) for r in result]
		return result
	
	def test(self):
		print(self.interpolation_cpw('mại', 'thương'))
