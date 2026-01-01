import os
from dotenv import load_dotenv
from flask import Flask, request
import requests

load_dotenv()
api_key = os.environ['webster_api_key']
app = Flask(__name__)

@app.route("/", methods=["GET"])
def word_entry():
    f = open("word_form.html")
    page = f.read()
    f.close()
    return page

@app.route('/lookup', methods=["POST"])
def lookup():
    word = request.form["word"]
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if isinstance(data[0], dict):
        definition = data[0]["shortdef"][0]
        
        f = open("p_dictionary.txt", "a")
        f.write(f"{word}: {definition}\n")
        f.close()
        
    
        return f"<h1>{word}</h1><p>{definition}</p><p>Word saved!</p>"
    else:
        return f"<p>'{word}' not found. Did you mean: {', '.join(data[:5])}</p>"

app.run(port=5000, debug=True)