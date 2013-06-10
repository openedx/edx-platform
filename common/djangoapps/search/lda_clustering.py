import os
import os.path as pt
import json
import csv

import gensim.corpora as corpus
from gensim import models
import gensim.similarities as similar
import re

from nltk.tokenize import word_tokenize as word_splitter
import nltk.data


def transcripts(sjson_directory):
    """Returns referenes to all of the files contained within a subs directory"""
    all_children = [child for child in os.listdir(sjson_directory)]
    all_transcripts = [child for child in all_children if pt.isfile(pt.join(sjson_directory, child))]
    uuids = [transcript_id[:transcript_id.find(".")] for transcript_id in all_transcripts]
    parsed_transcripts = [open(pt.join(sjson_directory, transcript)).read() for transcript in all_transcripts]
    tuple_filter = lambda x: x[0] is not ""
    results = filter(tuple_filter, zip([clean_transcript(transcript) for transcript in parsed_transcripts], uuids))
    return results


def clean_transcript(transcript_string):
    """Tries to parse and clean a raw transcript. Errors for invalid sjson"""
    try:
        transcript_list = filter(None, json.loads(transcript_string)['text'])
        relevant_text = " ".join([phrase.encode('utf-8').strip() for phrase in transcript_list])
        relevant_text = relevant_text.lower().translate(None, '"#$%&\'()*+,-/:;<=>@[\\]^_{|}~')
        cleanedText = re.sub('\n', " ", relevant_text)
        return cleanedText
    except:
        return ""


def sentences_to_tokens(sentence_list):
    words = []
    dummy = [words.extend(word_splitter(sentence)) for sentence in sentence_list]
    return words


def tokenize(transcripts, punkt):
    """Turns a the results of transcripts into a series of sentences"""
    sentences = [punkt.tokenize(transcript[0]) for transcript in transcripts]
    dummy = [(sentences_to_tokens(sentence)) for sentence in sentences]
    return dummy


def split_sentence(transcript):
    punkt = nltk.data.load("tokenizers/punkt/english.pickle")
    sentences = punkt.tokenize(transcript)
    return sentences_to_tokens(sentences)


def create_gensim_dictionary(directories, output_file):
    punkt = nltk.data.load('tokenizers/punkt/english.pickle')
    dictionary_seed = [tokenize(transcript, punkt) for transcript in [transcripts(subs) for subs in directories]]

    dictionary_seed = [item for sublist in dictionary_seed for item in sublist]
    dictionary = corpus.Dictionary(dictionary_seed)
    dictionary.save(output_file)


def corpus_generator(directories, dictionary_file="lda_start.dict", output_file="lda_start_corpus.mm"):
    punkt = nltk.data.load("tokenizers/punkt/english.pickle")
    dictionary = corpus.Dictionary.load(dictionary_file)
    corpus_seed = [tokenize(transcript, punkt) for transcript in [transcripts(subs) for subs in directories]]
    corpus_seed = [item for sublist in corpus_seed for item in sublist]
    transcript_corpus = [dictionary.doc2bow(text) for text in corpus_seed]
    corpus.MmCorpus.serialize(output_file, transcript_corpus)


def topic_extraction(topics=200, corpus_file="lda_start_corpus.mm", dictionary_file="lda_start.dict"):
    transcript_corpus = corpus.MmCorpus(corpus_file)
    dictionary = corpus.Dictionary.load(dictionary_file)
    tfidf = models.TfidfModel(transcript_corpus)
    corpus_tfidf = tfidf[transcript_corpus]
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=topics)
    return lsi


def transcript_vectorizer(lsi, transcript_corpus, course_list, dictionary, directories, node_file="nodes.csv", edge_file="edges.csv"):
    node_writer = csv.writer(open(node_file, 'wb'), delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
    edge_writer = csv.writer(open(edge_file, 'wb'), delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
    stepped_through = 0
    matches = 0
    index = similar.MatrixSimilarity(lsi[transcript_corpus])
    for i in range(0, len(directories)):
        course = course_list[i]
        directory = directories[i]
        all_children = [child for child in os.listdir(directory)]
        all_transcripts = [child for child in all_children if pt.isfile(pt.join(directory, child))]
        for j in range(0, len(all_transcripts)):
            transcript_string = open(pt.join(directory, all_transcripts[j])).read()
            tokens = split_sentence(clean_transcript(transcript_string))
            tokens = dictionary.doc2bow(tokens)
            transcript_lsi = lsi[tokens]
            tuple_vector = list(enumerate(index[transcript_lsi]))
            vector = [value[1] for value in tuple_vector]
            uuid = all_transcripts[j][:all_transcripts[j].find(".")]
            node_writer.writerow([j, course, uuid])
            stepped_through += 1
            for k in range(stepped_through, len(vector)):
                if vector[k] > 0.60:
                    matches += 1
                    print matches
                    edge_writer.writerow([j, k, vector[k]])


def node_list(directories, course_list, output_file="node_list.csv"):
    id_ = 1
    with open(output_file, 'wb') as data_dump:
        writer = csv.writer(data_dump, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(0, len(course_list)):
            course = course_list[0]
            directory = directories[0]
            all_children = [child for child in os.listdir(directory)]
            all_transcripts = [child for child in all_children if pt.isfile(pt.join(directory, child))]
            for transcript in all_transcripts:
                uuid = transcript[:transcript.find(".")]
                writer.writerow([id_, course, uuid])
                id_ += 1

base_directory = "/home/slater/edx_all/data/content-mit-"
biology = "802x"
ochem = "7012x"
circuits = "6002x"
math = "201x"
courses = [biology, ochem, circuits, math]
sub_directory = "/static/subs"
directories = [base_directory+directory+sub_directory for directory in courses]
lsi = topic_extraction()
transcript_corpus = corpus.MmCorpus("lda_start_corpus.mm")
dictionary = corpus.Dictionary.load("lda_start.dict")
transcript_vectorizer(lsi, transcript_corpus, courses, dictionary, directories)
#create_gensim_dictionary(directories)
#corpus_generator(directories, "lda_start.dict")
#topic_extraction()
