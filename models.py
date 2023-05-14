from database import db
from flask_login import UserMixin

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    passport = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    household_members = db.Column(db.Integer, nullable=False)
    kin_name = db.Column(db.String(100), nullable=False)
    kin_contact = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)

class DiasporaQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    query = db.Column(db.String(200), nullable=False)
