import os

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:ksv017.com@localhost/event_now')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key_here')  # Replace with a secure key in production