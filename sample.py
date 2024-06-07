import os
import re
import json
import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory, NIOFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import IndexOptions, IndexWriter, IndexWriterConfig, DirectoryReader
from org.apache.lucene.search import IndexSearcher

class LuceneIndex:
    def __init__(self, directory):
        self.directory = directory
        self.vm_env = None
        if not lucene.getVMEnv():
            self.vm_env = lucene.initVM(vmargs=['-Djava.awt.headless=true'])
        self.vm_env.attachCurrentThread()
        self.create_index(directory)

    def useMetaType(self, key: str):
        return key in ['permalink', 'id', 'url', 'score', 'upvote_ratio', 'created_utc', 'num_comments', 'author']

    def create_index(self, dir):
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

        regex = re.compile(r'.*\d+\.json')

        print(f"Indexing JSON files in {dir}")
        for filename in os.listdir(dir):
            if regex.fullmatch(filename):
                print(f"Indexing: {filename}")
                with open(os.path.join(dir, filename), 'r') as f:
                    writer.addDocument(doc)
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
                            elif self.useMetaType(key):
                                doc.add(Field(key, str(data), metaType))
                            else:
                                doc.add(Field(key, str(data), contextType))
                                context += str(data)
                        doc.add(Field("context", context, contextType))
                    
        writer.close()
        print("Indexing complete")

    def retrieve(self, query):
        print("Retrieving Documents")
        self.vm_env.attachCurrentThread()
        searchDir = NIOFSDirectory(Paths.get(self.directory))
        searcher = IndexSearcher(DirectoryReader.open(searchDir))
        parser = QueryParser('context', StandardAnalyzer())
        parsed_query = parser.parse(query)
        topDocs = searcher.search(parsed_query, 10).scoreDocs
        results = []
        print("Top 10 documents:")
        for hit in topDocs:
            doc = searcher.doc(hit.doc)
            results.append({
                'title': doc.get("title"),
                'content': doc.get("context")
            })
            print(doc.get("title"))
        print("Document retrieval complete")
        return results

# Initialize the Lucene index
directory = "/home/cs172/redditCrawler"
lucene_index = LuceneIndex(directory)

# Command line interface for testing
if __name__ == '__main__':
    query = "experiment"
    loop = True
    while loop:
        print("\nHit enter with no input to quit.")
        query = input("Enter a string: ")
        if query == '':
            loop = False
            break
        results = lucene_index.retrieve(query)
        for result in results:
            print(result)
