from connections import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events = db.relationship("Event", backref="creator", lazy=True, cascade="all, delete")
    registrations = db.relationship("EventRegistration", backref="user", lazy=True, cascade="all, delete")
    ratings = db.relationship("Rating", backref="user", lazy=True, cascade="all, delete")
    reminders = db.relationship("Reminder", backref="user", lazy=True, cascade="all, delete")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    events = db.relationship("Event", backref="category", lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=True)  # New field
    image_url = db.Column(db.String(255), nullable=True)  # New field for images
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)  # New field
    status = db.Column(db.String(20), default="Upcoming")  # New field: Upcoming, Ongoing, Past
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("EventRegistration", backref="event", lazy=True, cascade="all, delete")
    ratings = db.relationship("Rating", backref="event", lazy=True, cascade="all, delete")
    reminders = db.relationship("Reminder", backref="event", lazy=True, cascade="all, delete")

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=True)
    others = db.Column(db.Text, nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="unique_event_user_registration"),
        db.UniqueConstraint("event_id", "email", name="unique_event_email_registration"),
    )

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    rated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="valid_rating"),
        db.UniqueConstraint("user_id", "event_id", name="unique_user_event_rating"),
    )

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    reminder_time = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)