import os
import os.path as pt
import json
import re
import string

from pyes import *
import nltk.stem.snowball as snowball
import fuzzy
import nltk.data
from nltk.tokenize import word_tokenize as word_splitter


def grab_transcripts(sjson_directory):
    """Returns referenes to all of the files contained within a subs directory"""
    all_children = [child for child in os.listdir(sjson_directory)]
    all_transcripts = [child for child in all_children if pt.isfile(pt.join(sjson_directory, child))]
    # . is not a valid character for a youtube id, so it can be reliably used to pick up the start
    # of the file extension
    uuids = [transcript_id[:transcript_id.find(".")] for transcript_id in all_transcripts]
    parsed_transcripts = [open(pt.join(sjson_directory, transcript)).read() for transcript in all_transcripts]
    return zip([clean_transcript(transcript) for transcript in parsed_transcripts], uuids)


def clean_transcript(transcript_string):
    """Tries to parse and clean a raw transcript. Errors for invalid sjson"""
    transcript_list = filter(None, json.loads(transcript_string)['text'])
    relevant_text = " ".join([phrase.encode('utf-8').strip() for phrase in transcript_list])
    relevant_text = relevant_text.lower().translate(None, string.punctuation)
    cleanedText = re.sub('\n', " ", relevant_text)
    return cleanedText


def phonetic_transcript(clean_transcript, stemmer):
    return " ".join([phoneticize(word, stemmer) for word in clean_transcript.split(" ")])


def phoneticize(word, stemmer):
    encode = lambda word: word.decode('utf-8').encode('ascii', 'ignore')
    phonetic = lambda word: fuzzy.nysiis(stemmer.stem(encode(word)))
    return phonetic(word)


def initialize_transcripts(database, mapping):
    database.indices.create_index("transcript-index")


def index_course(database, sjson_directory, course_name, mapping):
    stemmer = snowball.EnglishStemmer()
    database.put_mapping(course_name, {'properties': mapping}, "transcript-index")
    all_transcripts = grab_transcripts(sjson_directory)
    video_counter = 0
    for transcript_tuple in all_transcripts:
        data_map = {"searchable_text": transcript_tuple[0], "uuid": transcript_tuple[1]}
        data_map['phonetic_text'] = phonetic_transcript(transcript_tuple[0], stemmer)
        database.index(data_map, "transcript-index", course_name)
        video_counter += 1
    database.indices.refresh("transcript-index")


def tokenize(transcript, punkt):
    """Turns a clean transcript string into a series of sentences"""
    print transcript
    sentences = punkt.tokenize(transcript)
    words = []
    words = [words.extend(word_splitter(sentence)) for sentence in sentences]
    return words


def fuzzy_search(database, query, course_name):
    search_query = FuzzyLikeThisFieldQuery("searchable_text", query)
    return database.search(query=search_query, indices="transcript-index")


def phonetic_search(database, query, course_name):
    stemmer = snowball.EnglishStemmer()
    search_query = TextQuery("phonetic_text", phoneticize(query, stemmer))
    return database.search(query=search_query, indices="transcript-index")


data_directory = '/Users/climatologist/edx_all/data/content-mit-6002x/static/subs/'
mapping_directory = 'mapping.json'
database = ES('127.0.0.1:9200')
mapping = json.loads(open(mapping_directory, 'rb').read())

#initialize_transcripts(database, mapping)
#index_course(database, data_directory, "test-course", mapping)
fuzzy_results = fuzzy_search(database, "gaussian", "test-course")
phonetic_results = phonetic_search(database, "gaussian", "test-course")
for r in fuzzy_results:
    print "Fuzzy: " + r['uuid']
for r in phonetic_results:
    print "Phonetic: " + r['uuid']
