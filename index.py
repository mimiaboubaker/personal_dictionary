import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, session, render_template
import requests
from datetime import date
import random
from werkzeug.security import generate_password_hash, check_password_hash

### This application has log in functionality but uses a shared database. In production, we'd need to add a database. 

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
    word = request.form["word"].strip().lower()
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
    if session.get("logged_in") == True: 
        word = session["word"]
        definition = session["definition"]
        part_of_speech = session["part_of_speech"] 
        current_date = date.today()
        
        with open("p_dictionary.txt", "a") as f:
            f.write(f"{current_date}|{part_of_speech}|{word}|{definition}\n")
        
        session.pop("word", None)
        session.pop("definition", None)
        session.pop("part_of_speech", None)  
        session.pop("study_list", None)
        
        return redirect("/")
    else:       
        return "Error: Must be logged in to save words. <a href='/login'>Log in here</a>" 
@app.route("/study", methods=["GET"])
def study():
    if session.get("logged_in") == True: 

        if not session.get('study_list'):
            study_list = []
            try:
                with open("p_dictionary.txt", "r") as f:
                    lines = f.readlines()
                
                for line in lines:
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        study_list.append({
                            'word': parts[2],
                            'definition': parts[3],
                            'part_of_speech': parts[1]
                        })
                
                random.shuffle(study_list)
                session["study_list"] = study_list
                
            except FileNotFoundError:
                pass
        else:
            study_list = session["study_list"]
        
        if len(study_list) > 0:
            current_word = study_list[0]  # ← First card from shuffled list
        else:
            current_word = None 

        cards_remaining = len(study_list)

        return render_template('study.html', word_count=len(study_list), current_word = current_word, cards_remaining = cards_remaining)
    else:
        return redirect("/")
@app.route("/repeat", methods=["POST"])
def repeat():
    if session.get("logged_in") == True: 
        study_list = session["study_list"]
        current_word = study_list.pop(0)

        # random position 
        position = random.randint(3, len(study_list))
        
        # insert current_word at random position point
        study_list.insert(position, current_word)

        # save session/update session and redirect
        session["study_list"] = study_list
        return redirect("/study")
    else: return redirect("/")
@app.route("/remove", methods=["POST"])
def remove():
    if session.get("logged_in") == True: 
        study_list = session["study_list"]
        current_word = study_list.pop(0)
        session["study_list"] = study_list
        return redirect("/study")
    else: 
        return redirect("/")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    
    if request.method == "POST":
        email = request.form["email"]
        email_confirmation = request.form["email-confirmation"]
        password = request.form["password"]
        password_confirmation = request.form["password-confirmation"]
        first_name = request.form["first-name"]
        last_name = request.form["last-name"]

    if email != email_confirmation:
        return "Error: Emails don't match! <a href='/register'>Try again</a>"
    
    if password != password_confirmation:
        return "Error: Passwords don't match! <a href='/register'>Try again</a>"

    user_exists = False
    
    try: 
        with open("users.txt", "r") as f:
            lines = f.readlines()

            for line in lines: 
                parts = line.strip().split("|")
                stored_email = parts[0]

                if stored_email == email: 
                    user_exists = True
                    break

    except FileNotFoundError:
        pass

    if user_exists:
        return "Error: Email already registered! <a href='/login'>Log in instead</a>"
    
    if user_exists == False:
        hashed_password = generate_password_hash(password)
        with open("users.txt", "a") as f:
            f.write(f"{email}|{hashed_password}|{first_name}|{last_name}\n")
    
    return redirect('/study')

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user_exists = False
        stored_password = None 
        
        try: 
            with open("users.txt", "r") as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split("|")
                stored_email = parts[0]
                
                if stored_email == email:
                    user_exists = True
                    stored_password = parts[1] 
                    break  
                    
        except FileNotFoundError:
            return "No users registered yet! <a href='/register'>Register here</a>"
        
        if not user_exists:
            return "Email not found! <a href='/register'>Register here</a>"
        
        if check_password_hash(stored_password, password):
            session["logged_in"] = True
            session["user_email"] = email
            return redirect("/study")
        else:
            return "Incorrect password! <a href='/login'>Try again</a>"
                
@app.route("/logout", methods=["GET"])
def logout():
    session.pop('logged_in', None)
    session.pop('user_email', None)
    return redirect ('/')






if __name__ == "__main__":
    app.run(debug=True)