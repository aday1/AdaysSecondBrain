from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AnxietyTrigger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    logs = db.relationship('AnxietyLog', backref='trigger', lazy=True)

class CopingStrategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    logs = db.relationship('AnxietyLog', backref='coping_strategy', lazy=True)

class AnxietyLog(db.Model):
    __tablename__ = 'anxiety_logs'  # Change to plural to match existing table
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    suds_score = db.Column(db.Integer, nullable=False)
    social_isolation = db.Column(db.Integer, default=0)
    insufficient_self_control = db.Column(db.Integer, default=0)
    subjugation = db.Column(db.Integer, default=0)
    negativity = db.Column(db.Integer, default=0)
    unrelenting_standards = db.Column(db.Integer, default=0)  # Match column name exactly
    trigger_id = db.Column(db.Integer, db.ForeignKey('anxiety_trigger.id'))
    coping_strategy_id = db.Column(db.Integer, db.ForeignKey('coping_strategy.id'))
    effectiveness = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)