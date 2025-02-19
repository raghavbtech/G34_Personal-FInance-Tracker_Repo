from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    bank_accounts = db.relationship('Bank', backref='user', lazy=True)
    transactions = db.relationship("Transaction", back_populates="user", lazy=True)  # 🔹 Establishes link to transactions


    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bankaccount = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    bname = db.Column(db.String(100), nullable=False)
    ifsc = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Bank account('{self.bankaccount}', '{self.name}', '{self.bname}', '{self.ifsc}')"
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # 🔹 Ensures transactions belong to users

    user = db.relationship("User", back_populates="transactions")  # 🔹 Optional relationship

