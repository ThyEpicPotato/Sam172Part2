import os
import re
import json
import lucene
from flask import Flask, request, jsonify
from java.nio.file import Paths
from org.apache.lucene.store import NIOFSDirectory, SimpleFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import IndexOptions, IndexWriter, IndexWriterConfig, DirectoryReader
from org.apache.lucene.search import IndexSearcher

app = Flask(__name__)

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
                writer.addDocument(doc)
    writer.close()
    print("Done Indexing")

def retrieve(storedir, query):
    print("Retrieving Documents")
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    parser = QueryParser('context', StandardAnalyzer())
    parsed_query = parser.parse(query)
    topDocs = searcher.search(parsed_query, 10).scoreDocs
    results = []
    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        result = {field.name(): doc.get(field.name()) for field in doc.getFields()}
        results.append(result)
    return results

def useMetaType(key):
    return key in ['permalink', 'id', 'url', 'score', 'upvote_ratio', 'created_utc', 'num_comments', 'author']

@app.route('/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if not query:
        return jsonify([])

    directory = "/home/cs172/redditCrawler"  # Update this to your actual directory containing the index
    results = retrieve(directory, query)
    return jsonify(results)

if __name__ == '__main__':
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    app.run(host='0.0.0.0', port=5000)  # Ensure this port is open on your server's firewall
