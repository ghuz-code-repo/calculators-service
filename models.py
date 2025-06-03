from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(50), nullable=False, default='user')

    
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

class CalculationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_full_name = db.Column(db.String(100), nullable=False)
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    apartment_id = db.Column(db.String(50), nullable=False)
    gd_discount = db.Column(db.Float, nullable=False)
    holding_discount = db.Column(db.Float, nullable=False)
    opt_discount = db.Column(db.Float, nullable=False)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    installment_period = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    cashback_value = db.Column(db.Float, nullable=False)

class Object(db.Model):
    __tablename__ = 'objects'
    apartment_id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    entrance = db.Column(db.Integer, nullable=False)
    apartment_number = db.Column(db.Integer, nullable=False)
    min_down_payment = db.Column(db.Float, nullable=False)
    max_down_payment = db.Column(db.Float, nullable=False)
    opt = db.Column(db.Float, nullable=False, default=0.0)
    holding = db.Column(db.Float, nullable=False, default=0.0)
    gd = db.Column(db.Float, nullable=False, default=0.0)  # Default to 0.0 if not provided
    max_discount = db.Column(db.Float, nullable=False, default=0.0)  # Default to 0.0 if not provided
    project = db.Column(db.String(100), nullable=False)
    kd= db.Column(db.Float, nullable=False, default=0.0)  # Default to 0.0 if not provided
    mpp= db.Column(db.Float, nullable=False, default=0.0)  # Default to 0.0 if not provided
    rop= db.Column(db.Float, nullable=False, default=0.0)  # Default to 0.0 if not provided


class Apartment(db.Model):
    __tablename__ = 'apartments'
    id = db.Column(db.Integer, primary_key=True)
    apartment_id = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=datetime.now)
    date_deleted = db.Column(db.DateTime, nullable=True, default=None)