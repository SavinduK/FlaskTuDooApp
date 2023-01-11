from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(75),unique=True)
    password = db.Column(db.String(75))
    date_created =db.Column(db.DateTime(timezone=True),default=func.now())

class Task(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    topic = db.Column(db.String())
    text = db.Column(db.String())
    category = db.column(db.String())
    user = db.Column(db.String())
    completed = db.Column(db.Integer)
    
class Image(db.Model):
   id = db.Column(db.Integer,primary_key=True)
   task_id = db.Column(db.Integer())
   user = db.Column(db.String())
   url = db.Column(db.String())
    
    
    
 

 
