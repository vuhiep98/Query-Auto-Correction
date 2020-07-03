import pandas as pd
from tqdm import tqdm

from corrector.dictionary import Dictionary
from corrector.segment import Segmentor
from corrector.correct import Corrector
from corrector.diacritic import DiacriticAdder
from corrector.ultis import *
from error_generator import ErrorGenrator

error_generator = ErrorGenrator(error_rate=0.05)

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


def auto_correct(error_queries, loop_index=-1):
    results = []
    for error_query in tqdm(error_queries):
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

    if loop_index >= 0:
        pd.DataFrame(results, columns=['input_query', 'label_query', 'output_query', 'prob']).to_csv(output_dir + 'results_' + str(loop_index) + '.csv', index=False)
    return results

def get_results_statistics(results, writer, loop_index=-1):
    right_corrected_queries = [res for res in results if res[1]==res[2]]
    accuracy = float(len(right_corrected_queries))/len(results)*100
    if loop_index >= 0:
        writer.write('Accuracy Loop {0}: {1:.2f}%\n'.format(loop_index, accuracy))
    return accuracy

def correct_error_auto_generating_queries(start_loop, end_loop):
    accuracy = []
    writer = open(output_dir + 'log_auto_genarating_errors_output.txt', 'w+', encoding='utf-8')

    for loop_index in range(start_loop, end_loop):
        data = pd.read_csv('data/error_auto_generated_queries/' + str(loop_index) + '.csv').values.tolist()
        results = auto_correct(data, loop_index)
        accuracy.append(get_results_statistics(results, writer, loop_index))
    writer.write('***********************************\nAverage accuracy: {0:.2f}%'.format(float(sum(accuracy))/len(accuracy)))
    writer.close()

def correct_non_diacritic_queries():
    input_file = 'data/700_non_diacritic_errors_file.csv'
    writer = open(output_dir + 'log_non_diacritic_error_output.txt', 'w+', encoding='utf-8')
    data = pd.read_csv(input_file).values.tolist()
    results = auto_correct(data)
    accuracy = get_results_statistics(results, writer)
    writer.write('Accuracy: {0:.2f}%\n'.format(accuracy))
    writer.close()

if __name__ == '__main__':
    
    correct_non_diacritic_queries()
    correct_error_auto_generating_queries(start_loop=5, end_loop=10)