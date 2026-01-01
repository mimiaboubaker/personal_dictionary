import requests, os
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

print("Environment variables loaded:")
print(os.environ.get('webster_key_api')) 

api_key = os.environ['webster_api_key']

@app.route("/", methods=["GET"])
def word_entry():
    form = request.form
    f = open("word_form.html", "r")
    page = f.read()
    f.close()
    return page


@app.route("/lookup", methods=["POST"])
def lookup():
    form = request.form
    word = form["word"]

    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}"

    response = requests.get(url)
    data = response.json()
    print(data)

app.run(port=5000, debug=True)
