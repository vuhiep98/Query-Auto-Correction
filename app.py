from flask import Flask, render_template, request, jsonify
import json
import pandas as pd
from tqdm import tqdm

from corrector.dictionary import Dictionary
from corrector.segment import Segmentor
from corrector.correct import Corrector
from corrector.diacritic import DiacriticAdder
from corrector.ultis import preprocess, post_process

app = Flask(__name__, static_folder='static')

dictionary = Dictionary()
segmentor = Segmentor()
corrector = Corrector()

dictionary.load_dict()
dictionary.create_cont_dict()
dictionary.load_diacritic_adder()
corrector.load_symspell()
# dictionary.load_context_dict()
diacritic_adder = DiacriticAdder()

@app.route('/query_auto_correction')
def get_home():
	return render_template('index.html', title='Query Auto Correction')

@app.route('/correct', methods=['POST'])
def correct():
	origin_query = request.json.get('query').lower()
	query, numbers = preprocess(origin_query)
	query = segmentor.segment(query)
	corrected_result = corrector.correct(query)
	diacritic_added_result = diacritic_adder.add_diacritic(result)
	corrected_result['result'] = post_process(corrected_result['result'], numbers)
	diacritic_added_result['result'] = post_process(diacritic_added_result['result'], numbers)
	return json.dumps({
	    'corrected': corrected_result,
	    'diacritic_added': diacritic_added_result
	})
