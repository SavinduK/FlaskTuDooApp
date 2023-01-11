from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
DB_NAME ="database.db"

def create_app():
 app = Flask(__name__)
 app.config['SECRET_KEY'] = "password"
 app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
 app.config['UPLOAD_FOLDER'] = "/imgs"
 db.init_app(app)
 csrf  = CSRFProtect(app)
 
 from .views import views
 from .auth import auth
 from .models import User,Task,Image

 create_database(app)
 csrf.exempt(views)
 csrf.exempt(auth)

 app.register_blueprint(views,url_prefix="/")
 app.register_blueprint(auth,url_prefix="/")

 login_manager = LoginManager()
 login_manager.login_view ="auth.login"
 login_manager.init_app(app)

 @login_manager.user_loader
 def load_user(id):
  return User.query.get(int(id))

 return app

def create_database(app):
 if not path.exists("website/"+DB_NAME):
  db.create_all(app=app)
  print("Database Created")
