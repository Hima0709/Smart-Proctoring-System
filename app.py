from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import subprocess
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "exam_system.db")

CHEATING_STATUS_FILE = "cheating_status.txt"

# Start video monitoring when exam starts
def start_cheating_detection():
    subprocess.Popen(["python", "cheating_detection.py"])

# Database Connection
def get_db_connection():
    print("Using DB at:", DB_PATH)   # for debugging
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/exam")
    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        question = request.form["question"]
        options = [request.form["option1"], request.form["option2"], request.form["option3"], request.form["option4"]]
        correct_answer = request.form["correct_answer"]
        cursor.execute("INSERT INTO questions (question, option1, option2, option3, option4, correct_answer) VALUES (?, ?, ?, ?, ?, ?)",
                       (question, *options, correct_answer))
        conn.commit()
    
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", questions=questions)

@app.route("/exam", methods=["GET", "POST"])
def exam():
    if "user_id" not in session or session.get("role") != "student":
        return redirect("/")

    # Start video monitoring
    start_cheating_detection()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()

    return render_template("exam.html", questions=questions)

@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "user_id" not in session or session.get("role") != "student":
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    
    score = 0
    total_questions = len(questions)

    for question in questions:
        user_answer = request.form.get(f"q{question['id']}", "")

        # Get correct answer using the stored option number
        correct_answer_index = int(question["correct_answer"])  # Convert stored "1,2,3,4" to int
        correct_answer_text = question[f"option{correct_answer_index}"]  # Get the actual text

        if user_answer == correct_answer_text:
            score += 1
    
    conn.close()
    return render_template("result.html", score=score, total=total_questions)

@app.route("/check_cheating")
def check_cheating():
    if os.path.exists(CHEATING_STATUS_FILE):
        with open(CHEATING_STATUS_FILE, "r") as f:
            status = f.read().strip()
        if status == "EXAM_TERMINATED":
            session.clear()  # Log out user
            return jsonify({"cheating": True, "message": "Cheating detected! Exam terminated."})
    return jsonify({"cheating": False})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
