from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    client_id = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, plaintext_password):
        self.password = generate_password_hash(plaintext_password)

    def check_password(self, plaintext_password):
        return check_password_hash(self.password, plaintext_password)
    
class ClientDashboard(db.Model):
    __tablename__ = 'client_dashboard'  # This must match your DB table name
    id = db.Column(db.Integer, primary_key=True)
    client_code = db.Column(db.String(50), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    investment_date = db.Column(db.Date, nullable=True)
    total_value = db.Column(db.Float, nullable=True)
    portfolio_value = db.Column(db.Float, nullable=True)
    return_pct = db.Column(db.Float, nullable=True)
    equity = db.Column(db.Float, nullable=True)
    mf = db.Column(db.Float, nullable=True)
    re = db.Column(db.Float, nullable=True)
    others = db.Column(db.Float)

    if isinstance(investment_date, datetime):
        investment_date = investment_date.date()  # convert datetime to date
