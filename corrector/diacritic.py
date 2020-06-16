import sys
from os.path import dirname, realpath

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from corrector.dictionary import Dictionary

class DiacriticAdder(Dictionary):
	def __init__(self):
		pass

	def _letter_cand(self, char):
		for line in self.diacritic:
			if char in line:
				return line
		return [char]

	def _word_cand(self, word):
		cands = [word]
		for i in range(len(word)):
			can_list = self._letter_cand(word[i])
			cands += [word[:i] + c + rest
						for c in can_list
						for rest in self._word_cand(word[i+1:])]
		return cands

	def _gen_cand(self, ob):
		if ob == '<num>':
			return [ob]
		cands = list(set(self._word_cand(ob)))
		cands = sorted(cands, key=lambda x: -self._c1w(x))[:min(10, len(cands))]
		return cands

	def _gen_states(self, obs):
		states = {}
		for ob in obs:
			states[ob] = self._gen_cand(ob)
		return states

	def _trans(self, cur, prev, prev_prev=None):
		if prev_prev is None:
			return self.cpw(cur, prev)
		else:
			return self.cp3w(cur, prev, prev_prev)

	def _emiss(self, cur_state, cur_observe):
		return 1/2*(self.words_similarity(cur_observe, cur_state) +\
				self.pw(cur_state))

	def _viterbi(self, states, obs):
		V = [{}]
		path = {}

		for st in states[obs[0]]:
			V[0][st] = 1.0
			path[st] = [st]

		for i in range(1, len(obs)):
			V.append({})
			new_path = {}

			for st in states[obs[i]]:
				prob, state = max([
						(V[i-1][prev_st]*self._trans(st, prev_st)*self._emiss(obs[i], st), prev_st)
						for prev_st in states[obs[i-1]]
				])

				V[i][st] = prob
				new_path[st] = path[state] + [st]

			path = new_path

		prob, state = max([(V[-1][st], st) for st in states[obs[-1]]])
		return {
			"prob": prob,
			"result": ' '.join(path[state])
		}


	def add_diacritic(self, text):
		obs = text.split()
		states = self._gen_states(obs)
		output = self._viterbi(states, obs)
		return output
