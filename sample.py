import time
import re
import json

import logging, sys
logging.disable(sys.maxsize)

import os
import lucene
from java.nio.file import Paths
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, NIOFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions, DirectoryReader
from org.apache.lucene.search import IndexSearcher, BoostQuery, Query
from org.apache.lucene.search.similarities import BM25Similarity

def useMetaType(key:str):
    if key == ('permalink' or 'id' or 'url' or 'score' or 'upvote_ratio' or 'created_utc' or 'num_comments' or 'author'):
        return True
    return False

def create_index(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
    print("Creating Index")
    store = SimpleFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)

    contextType = FieldType()
    contextType.setStored(True)
    contextType.setTokenized(True)
    contextType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    regex = re.compile('.*[1234567890]+\.json')

    print(f"Indexing jsons inside {dir}")
    for filename in os.listdir(dir):
        if regex.fullmatch(filename):
            print(f"Indexing: {filename}")
            with open(os.path.join(dir, filename), 'r') as f:
                data = json.load(f)
                for post in data:
                    # Mash everything into context for breadth search.
                    context = ""
                    doc = Document()
                    for key in post:
                        data = post[key]
                        if key == "comments":
                            for comment in data:
                                doc.add(Field('comment', str(comment), contextType))
                                context += str(comment)
                        elif useMetaType(key):
                            doc.add(Field(key, str(data), metaType))
                        else:
                            doc.add(Field(key, str(data), contextType))
                            context += str(data)

                    doc.add(Field("context", context, contextType))

                f.close()
                writer.addDocument(doc)
    writer.close()
    print("Done Indexing")

def retrieve(storedir, query):
    print("Retrieving Documents")
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))

    # Change context to the keys that are in the post<provide analyzer type for each key>
    parser = QueryParser('context', StandardAnalyzer())
    parsed_query = parser.parse(query)

    topDocs = searcher.search(parsed_query, 10).scoreDocs
    topkdocs = []
    print("Top 10 docs: ")
    i = 1
    for hit in topDocs:
        print(f"Document {i}: ")
        i += 1
        doc = searcher.doc(hit.doc)
        print(doc.get("title"))
    print("Done retrieving documents")
    return topkdocs

# need to change directory to match cs172 server directory
directory = "/home/cs172/redditCrawler"

lucene.initVM(vmargs=['-Djava.awt.headless=true'])
create_index(directory)
query = "experiment"
loop = True
while loop:
    print("\nHit enter with no input to quit.")
    while(isinstance(query, str)):
        query = input("Enter a string: ")
        if query == '':
            loop = False
            break

        topkDocs = retrieve(directory, query)