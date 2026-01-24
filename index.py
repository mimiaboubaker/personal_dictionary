import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, session
import requests
from datetime import date
import random

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
    
    page += "<div class='dictionary-section'>"
    page += "<h1 class='my-dictionary-heading'>My Dictionary</h1>"
    
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
            <div class="feed-of-words">
                <p class="date-saved">{date_saved}</p>
                <h3 class="word">{word}</h3>
                <p class="part-of-speech"><i>{part_of_speech}</i></p>
                <p class="definition">{definition}</p>
                
            </div>
            """
    except FileNotFoundError:
        page += "<p>No words saved yet!</p>"
    
    return page

@app.route('/lookup', methods=["POST"])
def lookup():
    word = request.form["word"]
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
    part_of_speech = session["part_of_speech"] 
    current_date = date.today()
    
    f = open("p_dictionary.txt", "a")
    f.write(f"{current_date}|{part_of_speech}|{word}|{definition}\n")
    f.close()
    
    session.pop("word", None)
    session.pop("definition", None)
    session.pop("part_of_speech", None)  
    
    return redirect("/")

@app.route("/study", methods=["GET"])
def study():
    if not session.get('words_to_test'):
        words_to_test = []
        try:
            f = open("p_dictionary.txt", "r")
            lines = f.readlines()
            f.close()
            
            print(f"Type of lines: {type(lines)}")  
            print(f"Total lines in file: {len(lines)}") 
            
            for line in lines:
                print(f"Processing line: {line}")
                parts = line.strip().split("|")
                print(f"Parts: {parts}, Length: {len(parts)}")
                if len(parts) >= 4:
                    word = parts[2]
                    definition = parts[3]
                    part_of_speech = parts[1]
                    words_to_test.append({
                        'word': word,
                        'definition': definition,
                        'part_of_speech': part_of_speech
                    })
                else:
                    print(f"Skipped line - not enough parts")
            
            session["words_to_test"] = words_to_test
            
        except FileNotFoundError:
            pass
    else:
        words_to_test = session["words_to_test"]
    
    f = open("study.html", "r")
    page = f.read()
    f.close()
    
    page += f"<p>Found {len(words_to_test)} words to study!</p>"
    
    return page
    

@app.route("/flashcards", methods=["GET"])
def flashcard():
    if not session.get('words_to_test'):
        words_to_test = []
        try:
            f = open("p_dictionary.txt", "r")
            lines = f.readlines()
            f.close()
            
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    words_to_test.append({
                        'word': parts[2],
                        'definition': parts[3],
                        'part_of_speech': parts[1]
                    })
        except FileNotFoundError:
            return "<p>No words saved yet!</p>"
        
        session["words_to_test"] = words_to_test
 
    else: 
        words_to_test = session["words_to_test"]

    if not session.get("current_word"):
        random_word = random.choice(words_to_test)
        session["current_word"] = random_word
        session["show_definition"] = False
    else:
        random_word = session["current_word"]     

    
    if not session.get("show_definition"):
    # State 1: Just show the word
        return f"""
            <h2>{random_word['word']}</h2>
            <p><i>{random_word['part_of_speech']}</i></p>
            <form method="POST" action="/reveal">
                <button type="submit">See Definition</button>
            </form>
        """
    else:
        # State 2: Show word + definition + buttons
        return f"""
            <h2>{random_word['word']}</h2>
            <p><i>{random_word['part_of_speech']}</i></p>
            <p>{random_word['definition']}</p>
            <form method="POST" action="/next">
                <button name="action" value="correct">✓ Mastered</button>
                <button name="action" value="review">✗ Review Again</button>
            </form>
        """

@app.route("/reveal", methods=["POST"])
def reveal(): 
    session["show_definition"] = True
    return redirect("/flashcards")

@app.route('/testing', methods=["GET"])
def testing(): 
    f = open("testing.html")
    page = f.read()
    f.close()

    return page

if __name__ == "__main__":
    app.run(debug=True)
