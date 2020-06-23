import pandas as pd
from tqdm import tqdm
from numpy import arange

from corrector.dictionary import Dictionary
from corrector.segment import Segmentor
from corrector.correct import Corrector
from corrector.diacritic import DiacriticAdder
from corrector.ultis import *
from error_generator import ErrorGenrator

error_generator = ErrorGenrator()

output_dir = 'data/Interpolation/'

def load_model(interpolation_lambda=1.):
    dictionary = Dictionary()
    dictionary.load_dict()
    dictionary.load_diacritic_adder()

    segmentor = Segmentor()

    corrector = Corrector()
    corrector.load_symspell()

    diacritic_adder = DiacriticAdder()
    dictionary.load_params([1, interpolation_lambda])

    return segmentor, corrector, diacritic_adder

def spelling_errors_auto_generate(correct_query_file):
    error_queries = []
    with open(correct_query_file, 'r', encoding='utf-8') as reader:
        for line in reader.readlines():
            query = line.replace('\n', '')
            error = error_generator.error(query)
            error_queries.append([error[1], error[0]])
    return error_queries


def auto_correct(error_queries, segmentor, corrector, diacritic_adder):
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

    return results

def get_results_statistics(results, writer, loop_index=-1):
    right_corrected_queries = [res for res in results if res[1]==res[2]]
    accuracy = float(len(right_corrected_queries))/len(results)*100
    if loop_index >= 0:
        writer.write('Accuracy Loop {0}: {1:.2f}%\n'.format(loop_index, accuracy))
    return accuracy

def correct_error_auto_generating_queries(loop):
    input_file = 'data/testing_input.txt'
    accuracy = []
    writer = open(output_dir + 'log_auto_genarating_errors_output.txt', 'w+', encoding='utf-8')

    segmentor, corrector, diacritic_adder = load_model(interpolation_lambda=1.)

    for loop_index in range(loop):
        error_queries = spelling_errors_auto_generate(input_file)
        results = auto_correct(error_queries, segmentor, corrector, diacritic_adder)
        accuracy.append(get_results_statistics(results, writer, loop_index))
    average_accuracy = float(sum(accuracy))/len(accuracy)
    writer.write('***********************************\nAverage accuracy: {0:.2f}%'.format(average_accuracy))
    writer.close()
    return average_accuracy

def correct_non_diacritic_queries():
    input_file = 'data/700_non_diacritic_errors_file.csv'
    writer = open(output_dir + 'log_non_diacritic_error_output.txt', 'w+', encoding='utf-8')

    data = pd.read_csv(input_file).values.tolist()
    segmentor, corrector, diacritic_adder = load_model(interpolation_lambda=1.)

    results = auto_correct(data, segmentor, corrector, diacritic_adder)
    accuracy = get_results_statistics(results, writer)
    writer.write('Accuracy: {0:.2f}%\n'.format(accuracy))
    writer.close()
    return accuracy

def inspect_interpolation_lambda(start, end, step, loop):
    k_writer = open(output_dir + 'log_interpolation.txt', 'w+', encoding='utf-8')
    error_queries = spelling_errors_auto_generate('data/testing_input.txt')
    for index in range(loop):
        k_writer.write('Loop {0}\n'.format(index))
        for k in arange(0.0, 1.01, 0.05):
            print(k)
            k_writer.write('k = {0:.2f}\n'.format(k))

            segmentor, corrector = load_model(interpolation_lambda=k)

            non_diacritic_accuracy = correct_non_diacritic_queries()
            auto_error_accuracy = correct_error_auto_generating_queries(1)

            k_writer.write('Non diactitic error accuracy: {0:2f}%\n'.format(non_diacritic_accuracy))
            k_writer.write('Auto errors accuracy: {0:.2f}%\n'.format(auto_error_accuracy))
        k_writer.write('********************\n')
    k_writer.close()
    correct_non_diacritic_queries()

if __name__ == '__main__':
    # k_writer = open(output_dir + 'log_interpolation.txt', 'w+', encoding='utf-8')
    # loop = 1
    # error_queries = spelling_errors_auto_generate('data/testing_input.txt')
    # for index in range(loop):
    #     k_writer.write('Loop {0}\n'.format(index))
    #     for k in arange(0.0, 1.01, 0.05):
    #         print(k)
    #         k_writer.write('k = {0:.2f}\n'.format(k))

    #         dictionary = Dictionary()
    #         dictionary.load_dict()
    #         dictionary.load_diacritic_adder()

    #         segmentor = Segmentor()

    #         corrector = Corrector()
    #         corrector.load_symspell()

    #         diacritic_adder = DiacriticAdder()
    #         dictionary.load_params([1, k])

    #         non_diacritic_accuracy = correct_non_diacritic_queries()
    #         auto_error_accuracy = correct_error_auto_generating_queries(error_queries)

    #         k_writer.write('Non diactitic error accuracy: {0:2f}%\n'.format(non_diacritic_accuracy))
    #         k_writer.write('Auto errors accuracy: {0:.2f}%\n'.format(auto_error_accuracy))
    #     k_writer.write('********************\n')
    # k_writer.close()
    # correct_non_diacritic_queries()
    correct_error_auto_generating_queries(loop = 5)