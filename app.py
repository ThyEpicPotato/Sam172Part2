# app.py
from flask import Flask, request, jsonify, render_template
import lucene
from sample import retrieve

app = Flask(__name__)

directory = "/home/cs172/redditCrawler"

# Initialize Lucene VM
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        results = retrieve(directory, query)
        return jsonify(results)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
