from flask import Flask, render_template, request, redirect, url_for, session, flash
from connections import db, init_db
from models import User, Category, Event, EventRegistration, Rating, Reminder
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
import functools # Import functools for creating decorators

app = Flask(__name__)
app.config.from_pyfile('config.py')
init_db(app)
migrate = Migrate(app, db)

# Decorator to check if user is logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'id' not in session:
            flash("Please log in to access this page!", "danger")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Helper function to update event status
def update_event_status(event):
    now = datetime.utcnow()
    if event.event_date > now:
        event.status = "Upcoming"
    elif event.event_date <= now <= event.event_date.replace(hour=23, minute=59):
        event.status = "Ongoing"
    else:
        event.status = "Past"
    db.session.commit()

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')

    query = Event.query
    if search:
        query = query.filter(Event.title.ilike(f'%{search}%') | Event.description.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)

    events = query.order_by(Event.event_date.asc()).paginate(page=page, per_page=5)
    for event in events.items:
        update_event_status(event)

    categories = Category.query.all()
    return render_template('index.html', events=events, categories=categories, search=search, category_id=category_id, status=status)

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['id']
    created_events = Event.query.filter_by(created_by=user_id).order_by(Event.event_date.asc()).all()
    registered_events = Event.query.join(EventRegistration).filter(EventRegistration.user_id == user_id).all()
    reminders = Reminder.query.filter_by(user_id=user_id).order_by(Reminder.reminder_time.asc()).all()

    for event in created_events + registered_events:
        update_event_status(event)

    return render_template('dashboard.html', created_events=created_events, registered_events=registered_events, reminders=reminders)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([name, email, password]):
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        if len(password) < 8 or not re.search(r'[A-Za-z].*\d|\d.*[A-Za-z]', password):
            flash("Password must be 8+ characters with letters and numbers!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "warning")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['id'] = user.id
            session['name'] = user.name
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid email or password!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for('login'))

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date_str = request.form.get('event_date')
        location = request.form.get('location')
        image_url = request.form.get('image_url')
        category_id = request.form.get('category_id', type=int)

        if not all([title, description, event_date_str]):
            flash("Title, description, and date are required!", "danger")
            return redirect(url_for('create_event'))

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
            if event_date < datetime.utcnow():
                flash("Event date must be in the future!", "danger")
                return redirect(url_for('create_event'))
        except ValueError:
            flash("Invalid date format! Use YYYY-MM-DDTHH:MM.", "danger")
            return redirect(url_for('create_event'))

        new_event = Event(
            title=title,
            description=description,
            event_date=event_date,
            location=location,
            image_url=image_url,
            category_id=category_id,
            created_by=session['id']
        )
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_event.html', categories=categories)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.created_by != session['id']:
        flash("You can only edit your own events!", "danger")
        return redirect(url_for('dashboard'))

    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date_str = request.form.get('event_date')
        location = request.form.get('location')
        image_url = request.form.get('image_url')
        category_id = request.form.get('category_id', type=int)

        if not all([title, description, event_date_str]):
            flash("Title, description, and date are required!", "danger")
            return redirect(url_for('edit_event', event_id=event_id))

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
            if event_date < datetime.utcnow():
                flash("Event date must be in the future!", "danger")
                return redirect(url_for('edit_event', event_id=event_id))
        except ValueError:
            flash("Invalid date format! Use YYYY-MM-DDTHH:MM.", "danger")
            return redirect(url_for('edit_event', event_id=event_id))

        event.title = title
        event.description = description
        event.event_date = event_date
        event.location = location
        event.image_url = image_url
        event.category_id = category_id
        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit_event.html', event=event, categories=categories)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.created_by != session['id']:
        flash("You can only delete your own events!", "danger")
        return redirect(url_for('dashboard'))

    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/join_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def join_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        others = request.form.get('others')

        if not all([name, email]):
            flash("Name and email are required!", "danger")
            return redirect(url_for('join_event', event_id=event_id))

        if EventRegistration.query.filter_by(event_id=event_id, user_id=session['id']).first():
            flash("You are already registered for this event!", "warning")
            return redirect(url_for('event_details', event_id=event_id))

        new_registration = EventRegistration(
            event_id=event_id,
            user_id=session['id'],
            name=name,
            email=email,
            phone=phone,
            others=others
        )
        db.session.add(new_registration)
        db.session.commit()
        flash("Successfully registered for the event!", "success")
        return redirect(url_for('dashboard'))

    return render_template('join_event.html', event=event)

@app.route('/event_details/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = EventRegistration.query.filter_by(event_id=event_id).all()
    ratings = Rating.query.filter_by(event_id=event_id).all()
    is_registered = False
    if session.get('id'): # Check for user ID in session to determine if logged in
        is_registered = bool(EventRegistration.query.filter_by(event_id=event_id, user_id=session['id']).first())
    update_event_status(event)
    return render_template('event_details.html', event=event, registrations=registrations, ratings=ratings, is_registered=is_registered)

@app.route('/rate_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def rate_event(event_id):
    event = Event.query.get_or_404(event_id)
    existing_rating = Rating.query.filter_by(user_id=session['id'], event_id=event_id).first()

    if request.method == 'POST':
        if existing_rating:
            flash("You have already rated this event!", "warning")
            return redirect(url_for('event_details', event_id=event_id))

        rating = request.form.get('rating')
        comment = request.form.get('comment')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            flash("Rating must be a number between 1 and 5!", "danger")
            return redirect(url_for('rate_event', event_id=event_id))

        new_rating = Rating(
            user_id=session['id'],
            event_id=event_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_rating)
        db.session.commit()
        flash("Event rated successfully!", "success")
        return redirect(url_for('event_details', event_id=event_id))

    return render_template('rate_event.html', event=event)

@app.route('/set_reminder/<int:event_id>', methods=['GET', 'POST'])
@login_required
def set_reminder(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        reminder_time_str = request.form.get('reminder_time')
        message = request.form.get('message')

        try:
            reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M')
            if reminder_time >= event.event_date:
                flash("Reminder time must be before the event starts!", "danger")
                return redirect(url_for('set_reminder', event_id=event_id))
            if reminder_time < datetime.utcnow():
                flash("Reminder time must be in the future!", "danger")
                return redirect(url_for('set_reminder', event_id=event_id))
        except ValueError:
            flash("Invalid date format! Use YYYY-MM-DDTHH:MM.", "danger")
            return redirect(url_for('set_reminder', event_id=event_id))

        new_reminder = Reminder(
            user_id=session['id'],
            event_id=event_id,
            reminder_time=reminder_time,
            message=message
        )
        db.session.add(new_reminder)
        db.session.commit()
        flash("Reminder set successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('set_reminder.html', event=event)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    # Seed initial categories (run once)
    with app.app_context():
        if not Category.query.first():
            categories = ["Workshop", "Party", "Conference", "Meetup"]
            for name in categories:
                db.session.add(Category(name=name))
            db.session.commit()
    app.run(debug=True)