import os, re, string, json
from tqdm import tqdm
from collections import Counter

DIGIT = '<num>'
DATA_FOLDER = 'STM project/'
MODEL_PATH = 'model/new_content/'

def encode_numbers(text):
	text = re.sub(r'[\S]*\d+[\S]*', DIGIT, text)
	return text

def preprocess(text):
	text = text.strip().lower()
	text = encode_numbers(text)
	return text
	
def read_about(folder_number):
	abouts = []
	for i in range(folder_number*10000, (folder_number+1)*10000):
		file_directory = DATA_FOLDER + 'data_original_files' + \
						  str(folder_number*10000) + '-' + \
						  str((folder_number+1)*10000-1) + '/' + \
						  str(i) + '_about.txt'
		if os.path.isfile(file_directory):
			reader = open(file_directory, 'r', encoding='utf-8')
			abouts += [preprocess(' '.join(reader.readlines()))]
	return abouts

def drop_na(sent):
	return True if sent not in ['', DIGIT] else False

def read_content(content_path):
	if os.path.isfile(content_path):
		sentences = []
		with open(content_path, 'r', encoding='utf-8') as reader:
			lines = [re.sub(r'\s{2,}|\t+', ' ', encode_numbers(line.lower())) for line in reader.readlines() if "|" not in line]
			lines = ['<break>\n' if line == '\n' else line for line in lines]
			lines = [line.replace('\n', ' ') for line in lines]
			content = "".join(lines)
			sents = re.split(r'<break>|[.;:?]', content)
			for sent in sents:
				tokens = re.findall(r'<num>|\b\S+\b', sent)
				tokens = [''.join(re.findall(r'\w+', token)) if token!='<num>' else token for token in tokens]
				sentences.append(tokens)
			return sentences
	else:
		return []

def preprocess_about_data():
	start = 0
	end = 50

	unigrams = {}
	bigrams = {}
	trigrams = {}

	for i in tqdm(range(start, end+1), desc="Process abouts"):
		for about in read_about(i):
			tokens = re.findall(r'<num>|\w+')
			for j in range(len(tokens)):
				if tokens[j] not in unigrams:
					unigrams[tokens[j]] = 1
				else:
					unigrams[tokens[j]] += 1

				if j < len(tokens)-2:
					bigram = " ".join(tokens[j:j+2])
					if bigram not in bigrams:
						bigrams[bigram] = 1
					else:
						bigrams[bigram] += 1

				if j < len(tokens)-3:
					trigram = " ".join(tokens[j:j+3])
					if trigram not in trigrams:
						trigrams[trigram] = 1
					else:
						trigrams[trigram] +=1
	
	unigrams = {k:v for k, v in sorted(unigrams.items(), key=lambda x: x[1])}
	bigrams = {k:v for k, v in sorted(bigrams.items(), key=lambda x: x[1])}
	trigrams = {k:v for k, v in sorted(trigrams.items(), key=lambda x: x[1])}

	with open(MODEL_PATH + 'unigrams.txt', 'w+', encoding='utf-8') as writer:
		for k, v in unigrams.items():
			writer.write(k + ' ' + str(v) + '\n')

	with open(MODEL_PATH + 'bigrams.txt', 'w+', encoding='utf-8') as writer:
		for k, v in bigrams.items():
			writer.write(k + ' ' + str(v) + '\n')

	with open(MODEL_PATH + 'trigrams.txt', 'w+', encoding='utf-8') as writer:
		for k, v in trigrams.items():
			writer.write(k + ' ' + str(v) + '\n')


def preprocess_content_data(start=0, end=10):

	unigrams = {}
	bigrams = {}
	trigrams = {}

	for i in range(start, end+1):
		for j in tqdm(range(i*10000, (i+1)*10000), desc=str(i), ascii=True):
			for sent in read_content(DATA_FOLDER + 'data_original_files' + str(i*10000) + '-' + str((i+1)*10000-1) + \
									 '/' + str(j) + '_content.txt'):
				words = ['<START>'] + sent.split() + ['<END>']
				for index, w in enumerate(words):
					if index < len(words)-2:
						if w+' '+words[index+1]+' '+words[index+2] in trigrams: trigrams[w+' '+words[index+1]+' '+words[index+2]] += 1
						else: trigrams[w+' '+words[index+1]+' '+words[index+2]] = 1
					if index < len(words)-1:
						if w+' '+words[index+1] in bigrams: bigrams[w+' '+words[index+1]] += 1
						else: bigrams[w+' '+words[index+1]] = 1
					if w in unigrams: unigrams[w] += 1
					else: unigrams[w] = 1

	cnt_uni = sorted(Counter(unigrams).items(), key=lambda x: x[1], reverse=True)
	cnt_bi = sorted(Counter(bigrams).items(), key=lambda x: x[1], reverse=True)
	cnt_tri = sorted(Counter(trigrams).items(), key=lambda x: x[1], reverse=True)

	with open(MODEL_PATH + 'unigrams' + str(start) + '_' + str(end) + '.txt', 'w+', encoding='utf-8') as writer:
		for uni in cnt_uni:
			writer.write(str(uni[0]) + ' ' + str(uni[1]) + '\n')

	with open(MODEL_PATH + 'bigrams' + str(start) + '_' + str(end) + '.txt', 'w+', encoding='utf-8') as writer:
		for bi in cnt_bi:
			writer.write(str(bi[0]) + ' ' + str(bi[1]) + '\n')

	with open(MODEL_PATH + 'trigrams' + str(start) + '_' + str(end) + '.txt', 'w+', encoding='utf-8') as writer:
		for tri in cnt_tri:
			writer.write(str(tri[0]) + ' ' + str(tri[1]) + '\n')

def generate_context_dict():
	trigrams = {}
	context_dict = {}
	with open(MODEL_PATH + "trigrams.txt", "r", encoding="utf-8") as reader:
		for line in tqdm(reader.readlines(), desc="Load trigrams for context dictionary"):
			last_space = line.rindex(" ")
			key, value = line[:last_space], int(line[last_space+1:])
			trigrams[key] = value
	
	for tri in tqdm(trigrams, desc="Build context dictionary"):
		tokens = tri.split('_')
		context = tokens[0] + " " + tokens[2]
		if tokens[1] not in context_dict:
			context_dict[tokens[1]] = {context: trigrams[tri]}
		elif context not in context_dict[tokens[1]]:
			context_dict[tokens[1]][context] = trigrams[tri]
		else:
			context_dict[tokens[1]][context] += trigrams[tri]
	
	with open(MODEL_PATH + "context_dict.txt", "w+", encoding="utf-8") as writer:
		writer.write(json.dumps(context_dict, indent=4, ensure_ascii=False))

if __name__ == '__main__':
	# preprocess_data(0, 10)
	generate_context_dict()
	# preprocess_about_data()