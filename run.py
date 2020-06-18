import pandas as pd
from tqdm import tqdm

from corrector.dictionary import Dictionary
from corrector.segment import Segmentor
from corrector.correct import Corrector
from corrector.diacritic import DiacriticAdder
from corrector.ultis import *
from error_generator import ErrorGenrator

error_generator = ErrorGenrator()

dictionary = Dictionary()
dictionary.load_dict()
dictionary.create_cont_dict()
dictionary.load_diacritic_adder()

segmentor = Segmentor()

corrector = Corrector()
corrector.load_symspell()

diacritic_adder = DiacriticAdder()

output_dir = 'data/Kneser-Ney/'

def spelling_errors_auto_generate(correct_query_file):
    error_queries = []
    with open(correct_query_file, 'r', encoding='utf-8') as reader:
        for line in reader.readlines():
            query = line.replace('\n', '')
            error = error_generator.error(query)
            error_queries.append([error[1], error[0]])
    return error_queries


def auto_correct(error_queries, loop_index):
    results = []
    for error_query in error_queries:
        query, numbers = preprocess(error_query[0])
        segmented_query = segmentor.segment(query)

        corrected_query = corrector.correct(segmented_query)
        corrected_query['result'] = post_process(corrected_query['result'], numbers)

        diacritic_added_query = diacritic_adder.add_diacritic(segmented_query)
        diacritic_added_query['result'] = post_process(diacritic_added_query['result'], numbers)

        if corrected_query['prob'] >= diacritic_added_query['prob']:
            output_result = corrected_query['result']
            output_prob = corrected_query['prob']
        else:
            output_result = diacritic_added_query['result']
            output_prob = diacritic_added_query['prob']

        results.append([error_query[0], error_query[1], output_result, output_prob])

    pd.DataFrame(results, columns=['input_query', 'label_query', 'output_query', 'prob']).to_csv(output_dir + 'results_' + str(loop_index) + '.csv', index=False)
    return results

def get_results_statistics(results, loop_index):
    right_corrected_queries = [res for res in results if res[1]==res[2]]
    accuracy = float(len(right_corrected_queries))/len(results)*100
    print('Accuracy Loop {0}: {1:.2f}%'.format(loop_index, accuracy))
    return accuracy

if __name__ == '__main__':
     
    loop = 10
    input_file = 'data/testing_input.txt'
    accuracy = []

    for index in range(loop):
        error_queries = spelling_errors_auto_generate(input_file)
        results = auto_correct(error_queries, index)
        accuracy.append(get_results_statistics(results, index))
    
    print('***********************************\nAverage accuracy: {0:.2f}%'.format(float(sum(accuracy))/len(accuracy)))