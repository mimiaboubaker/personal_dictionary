import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, session, render_template
import requests
from datetime import date
import random

load_dotenv()
api_key = os.environ['webster_api_key']

app = Flask(__name__)
app.secret_key = os.environ["sessions_secret_key"]

@app.route("/", methods=["GET"])
def word_entry():
    # Get current word if it exists
    current_word = None
    if session.get("word"):
        current_word = {
            'word': session["word"],
            'definition': session["definition"],
            'part_of_speech': session.get("part_of_speech", "unknown")
        }
    
    # Get all saved dictionary entries
    entries = []
    try:
        with open("p_dictionary.txt", "r") as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            parts = line.strip().split("|")
            if len(parts) >= 4:
                entries.append({
                    'date': parts[0],
                    'part_of_speech': parts[1],
                    'word': parts[2],
                    'definition': parts[3]
                })
    except FileNotFoundError:
        pass
    
    return render_template('word_form.html', 
                         current_word=current_word,
                         entries=entries)

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
    
    with open("p_dictionary.txt", "a") as f:
        f.write(f"{current_date}|{part_of_speech}|{word}|{definition}\n")
    
    session.pop("word", None)
    session.pop("definition", None)
    session.pop("part_of_speech", None)  
    
    return redirect("/")

@app.route("/study", methods=["GET"])
def study():
    if not session.get('words_to_test'):
        words_to_test = []
        try:
            with open("p_dictionary.txt", "r") as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    words_to_test.append({
                        'word': parts[2],
                        'definition': parts[3],
                        'part_of_speech': parts[1]
                    })
            
            session["words_to_test"] = words_to_test
            
        except FileNotFoundError:
            pass
    else:
        words_to_test = session["words_to_test"]
    
    return render_template('study.html', word_count=len(words_to_test))

@app.route("/flashcards", methods=["GET"])
def flashcard():
    if not session.get('words_to_test'):
        words_to_test = []
        try:
            with open("p_dictionary.txt", "r") as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    words_to_test.append({
                        'word': parts[2],
                        'definition': parts[3],
                        'part_of_speech': parts[1]
                    })
        except FileNotFoundError:
            return render_template('flashcards.html', no_words=True)
        
        session["words_to_test"] = words_to_test
    else: 
        words_to_test = session["words_to_test"]

    if not session.get("current_word"):
        random_word = random.choice(words_to_test)
        session["current_word"] = random_word
        session["show_definition"] = False
    else:
        random_word = session["current_word"]

    return render_template('flashcards.html',
                         current_word=random_word,
                         show_definition=session.get("show_definition", False))

@app.route("/reveal", methods=["POST"])
def reveal(): 
    session["show_definition"] = True
    return redirect("/flashcards")

@app.route("/next", methods=["POST"])
def next_card():
    action = request.form.get("action")
    
    # Handle the action (mastered vs review)
    # You can add logic here to track progress
    
    # Clear current word to get a new one
    session.pop("current_word", None)
    session["show_definition"] = False
    
    return redirect("/flashcards")

if __name__ == "__main__":
    app.run(debug=True)