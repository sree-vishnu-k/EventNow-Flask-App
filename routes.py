from flask import Flask, render_template, request, redirect, url_for, session, flash
from connection import db, init_db
from models import User, Event, EventRegistration, Rating, Reminder  # Ensure these models are defined in models.py
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config.from_object("config")
app.secret_key = "your_secret_key"  # Replace with a secure key
init_db(app)

@app.route("/")
def home():
    events = Event.query.all()
    return render_template("index.html", events=events)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        # Hash the password to match the stored format
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            flash("Invalid login credentials", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Using 'name' instead of 'username' to match the models
        name = request.form["name"]
        email = request.form["email"]
        # Hash the password before storing it
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if "user_id" not in session:
        flash("You must be logged in to create an event!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        event_date = datetime.strptime(request.form["date"], "%Y-%m-%dT%H:%M")  # Ensure the form input matches this format
        event_date = datetime.strptime(request.form["date"], "%Y-%m-%dT%H:%M")
        created_by = session["user_id"]

        new_event = Event(title=title, description=description, event_date=event_date, created_by=created_by)
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully!", "success")
        return redirect(url_for("home"))

    return render_template("create_event.html")

if __name__ == "__main__":
    app.run(debug=True)
