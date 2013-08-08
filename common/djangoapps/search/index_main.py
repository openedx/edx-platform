"""
Main method for running indexing operations from the command line.
"""

import sys
from es_requests import MongoIndexer
from es_requests import ElasticDatabase

if sys.argv[1] == "regenerate":
    MONGO = MongoIndexer(content_database="edge-xcontent", module_database="edge-xmodule")
    MONGO2 = MongoIndexer()

    EDB = ElasticDatabase()

    if "pdf" in sys.argv[2:]:
        print EDB.delete_index("pdf-index")
        MONGO.index_all_pdfs("pdf-index")
        MONGO2.index_all_pdfs("pdf-index")

    if "transcript" in sys.argv[2:]:
        print EDB.delete_index("transcript-index")
        MONGO.index_all_transcripts("transcript-index")
        MONGO2.index_all_transcripts("transcript-index")

    if "problem" in sys.argv[2:]:
        print EDB.delete_index("problem-index")
        MONGO.index_all_problems("problem-index")
        MONGO2.index_all_problems("problem-index")
