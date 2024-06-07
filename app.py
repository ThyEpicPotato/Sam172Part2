from flask import Flask, render_template, request, jsonify
from sample import retrieve

app = Flask(__name__)

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for the search functionality
@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return jsonify([])

    try:
        directory = "/path/to/your/index/directory"
        results = retrieve(directory, query)
    except Exception as e:
        print(f"Error: {e}")
        results = []

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888) 
