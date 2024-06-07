# app.py
from flask import Flask, request, jsonify, render_template
from sample import lucene_index

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        results = lucene_index.retrieve(query)
        formatted_results = [{
            'title': res['title'],
            'content': (res['content'][:200] + '...') if len(res['content']) > 200 else res['content'],
            'permalink': res.get('permalink', '#')
        } for res in results[:10]]
        return jsonify(formatted_results)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)
