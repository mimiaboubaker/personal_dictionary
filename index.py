import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, session
import requests
from datetime import date

load_dotenv()
api_key = os.environ['webster_api_key']

app = Flask(__name__)
app.secret_key = os.environ["sessions_secret_key"]

@app.route("/", methods=["GET"])
def word_entry():
    f = open("word_form.html")
    page = f.read()
    f.close()
    
    if session.get("word"):
        word = session["word"]
        definition = session["definition"]
        part_of_speech = session.get("part_of_speech", "unknown")
        page += f"<h2>{word}</h2><p><i>{part_of_speech}</i></p><p>{definition}</p>"
        page += """
        <form method="POST" action="/save">
            <button type="submit">Save to Dictionary</button>
        </form>"""
    
    page += "<hr><h2>My Dictionary</h2>"
    
    try:
        f = open("p_dictionary.txt", "r")
        lines = f.readlines()
        f.close()
        
        for line in reversed(lines):
            parts = line.strip().split("|")
            date_saved = parts[0]
            part_of_speech = parts[1]
            word = parts[2]
            definition = parts[3]
            
            page += f"""
            <div>
                <p>{date_saved}</p>
                <h2>{word}</h2>
                <p><i>{part_of_speech}</i></p>
                <p>{definition}</p>
                <hr>
            </div>
            """
    except FileNotFoundError:
        page += "<p>No words saved yet!</p>"
    
    return page

@app.route('/lookup', methods=["POST"])
def lookup():
    word = request.form["word"].lower()
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if isinstance(data[0], dict):
        definition = data[0]["shortdef"][0]
        part_of_speech = data[0]["fl"]
        session["word"] = word
        session["definition"] = definition
        session["part_of_speech"] = part_of_speech
        return redirect("/")
    else:
        return f"<p>'{word}' not found. Did you mean: {', '.join(data[:5])}</p>"

@app.route("/save", methods=["POST"])
def save_to_dictionary():
    word = session["word"]
    definition = session["definition"]
    part_of_speech = session["part_of_speech"]  # Added this!
    current_date = date.today()
    
    f = open("p_dictionary.txt", "a")
    f.write(f"{current_date}|{part_of_speech}|{word}|{definition}\n")
    f.close()
    
    session.pop("word", None)
    session.pop("definition", None)
    session.pop("part_of_speech", None)  # Clear this too!
    
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)