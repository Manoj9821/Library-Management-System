import os
import random
from datetime import date
from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

# ----------------- Flask App -----------------
app = Flask(__name__)
app.secret_key = "your_secret_key"

# ----------------- Flask-Mail Setup -----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'      # change
app.config['MAIL_PASSWORD'] = 'your_email_password'       # change
mail = Mail(app)

# -------------- MySQL Connection ----------------
DB_NAME = "library_project"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="library_project",
        port=3307
    )

# ----------------- Utility: send OTP email -----------------
def send_otp(email):
    otp = random.randint(100000, 999999)
    session['otp'] = str(otp)
    session['otp_email'] = email
    msg = Message("Your OTP Code - Library", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"Your OTP for Library verification/reset is: {otp}"
    mail.send(msg)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Routes -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):

            # Save session values
            session["email"] = email
            session["role"] = user["role"]   # <-- IMPORTANT: stores admin/user

            # DIFFERENTIATE ADMIN VS USER ROUTE
            if user["role"] == "admin":
                return redirect("/admin_dashboard")
            else:
                return redirect("/user_dashboard")

        flash("Invalid login credentials")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_pass = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
            (email, hashed_pass, "user")
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Registration successful! Please login.")
        return redirect("/login")

    return render_template("register.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    if "role" in session and session["role"] == "admin":
        return render_template("admin_dashboard.html")
    return "Access Denied", 403

@app.route("/add_books")
def add_books():
    return render_template("add_books.html")

@app.route("/issued_books")
def issued_books():
    return render_template("issued_books.html")

@app.route("/returned_books")
def returned_books():
    return render_template("returned_books.html")

@app.route("/user_dashboard")
def user_dashboard():
    if "email" not in session:
        return redirect("/login")
    if session.get("role") != "user":
        return redirect("/admin_dashboard")

    return render_template("user_dashboard.html")

@app.route("/view_books")
def view_books():
    if "email" not in session:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("view_books.html", books=books)

@app.route("/search_books", methods=["GET", "POST"])
def search_books():
    if "email" not in session:
        return redirect("/login")

    books = []

    if request.method == "POST":
        keyword = request.form["keyword"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s",
            (f"%{keyword}%", f"%{keyword}%")
        )
        books = cursor.fetchall()
        cursor.close()
        db.close()

    return render_template("search_books.html", books=books)

@app.route("/search_question_papers", methods=["GET", "POST"])
def search_question_papers():
    results = []

    if request.method == "POST":
        subjectcode = request.form.get("subjectcode")
        years = request.form.get("years")

        if subjectcode and years:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM question_papers WHERE subjectcode=%s AND years=%s",
                (subjectcode, years)
            )

            results = cursor.fetchall()
            cursor.close()
            db.close()

    return render_template("search_question_papers.html", results=results)


@app.route("/view_question_papers")
def view_question_papers():
    if "email" not in session:
        
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM question_papers")
    papers = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("view_question_papers.html", papers=papers)

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect("/login")

    role = session["role"]

    if role == "admin":
        return render_template("admin_dashboard.html")

    if role == "user":
        return render_template("user_dashboard.html")

    return "Invalid role"


@app.route("/search")
def search():
    return render_template("search_results.html")

@app.route("/filter")
def filter_results():
    return render_template("filter_results.html")

@app.route("/profile")
def profile():
    return render_template("user.html")

@app.route("/upload_qp", methods=["GET", "POST"])
def upload_qp():
    if request.method == "POST":

        subjectcode = request.form["subjectcode"]
        years = request.form["years"]
        file = request.files["qpfile"]

        if file.filename == "":
            return render_template("upload_qp.html", error="No file selected")

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO question_papers (subjectcode, years, file) VALUES (%s, %s, %s)",
            (subjectcode, years, filename)
        )

        db.commit()
        cursor.close()
        db.close()

        return render_template("upload_qp.html", error="Uploaded successfully")

    return render_template("upload_qp.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ----------------- Password Reset -----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            send_otp(email)
            flash("OTP sent to your email")
            return redirect("/verify-otp")

        flash("Email not registered")

    return render_template("forgot_password.html")


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if "otp" in session and entered_otp == session["otp"]:
            flash("OTP verified successfully!")
            return redirect("/reset-password")

        flash("Invalid OTP")

    return render_template("verify_otp.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_pass = request.form["password"]

        if "otp_email" in session:
            email = session["otp_email"]

            db = get_db_connection()
            cursor = db.cursor()
            hashed_pass = generate_password_hash(new_pass)

            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pass, email))
            db.commit()
            cursor.close()
            db.close()

            session.pop("otp", None)
            session.pop("otp_email", None)

            flash("Password reset successful! Login now.")
            return redirect("/login")

        flash("Session expired, try again")
        return redirect("/forgot-password")

    return render_template("reset_password.html")


# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
