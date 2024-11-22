#from app import app, db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()




class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    experiments = db.relationship('Experiment', backref='user', lazy=True)

    # 入力されたパスワードが登録されているパスワードハッシュと一致するかを確認
    def check_password(self, password):
            return check_password_hash(self.password, password)


class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False,unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_code = db.Column(db.String(50))
    create_at = db.Column(db.DateTime(timezone=True),default=db.func.now())
    runs = db.relationship('Run', backref='experiment', lazy=True)


class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    name = db.Column(db.String(100))
    type = db.Column(db.String(50))
    create_at = db.Column(db.DateTime,default=db.func.now())
    inputs = db.relationship('Input', backref='run', lazy=True)
    buffers = db.relationship('Buffer', backref='run', lazy=True)
    fractions = db.relationship('Fraction', backref='run', lazy=True)
    pages = db.relationship('Page', backref='run', lazy=True)
    worksheetlink = db.relationship('Worksheetlink', backref='run', lazy=True)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    create_at = db.Column(db.DateTime,default=db.func.now())


class Reagent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    molecular_amount = db.Column(db.Float)


class Input(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'), nullable=False)
    name = db.Column(db.String(100))


class Buffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    place = db.Column(db.String(50))
    reagent_id = db.Column(db.Integer, db.ForeignKey('reagent.id'), nullable=False)
    amount = db.Column(db.Float)


class Fraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    fraction_id = db.Column(db.Integer)  # Consider renaming for clarity
    name = db.Column(db.String(100))
    create_at = db.Column(db.DateTime,default=db.func.now())
    links = db.relationship('Link', backref='fraction', lazy=True)


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    lane_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    links = db.relationship('Link', backref='page', lazy=True)
    peaks = db.relationship('Peak', backref='page', lazy=True)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fraction_id = db.Column(db.Integer, db.ForeignKey('fraction.id'), nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)


class Peak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    peak = db.Column(db.Float)  # Consider renaming to something more descriptive


class Worksheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    name = db.Column(db.String(100))
    type = db.Column(db.String(50))
    create_at = db.Column(db.DateTime,default=db.func.now())
    worksheetlink = db.relationship('Worksheetlink', backref='worksheet', lazy=True)


class Worksheetlink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worksheet_id = db.Column(db.Integer, db.ForeignKey('worksheet.id'), nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)