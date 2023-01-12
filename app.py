from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from flask import Blueprint,render_template,url_for,redirect,request,jsonify,flash
from flask_login import login_user,logout_user,login_required,current_user,UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from fileinput import filename
import sys
import os
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func

auth = Blueprint("auth",__name__)
views = Blueprint("views",__name__)

db = SQLAlchemy()
DB_NAME ="database.db"


app = Flask(__name__)
app.config['SECRET_KEY'] = "password"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['UPLOAD_FOLDER'] = "/imgs"
db.init_app(app)

app.register_blueprint(views,url_prefix="/")
app.register_blueprint(auth,url_prefix="/")

login_manager = LoginManager()
login_manager.login_view ="login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
   return User.query.get(int(id))



#--------------------------------------------------------------------------------------
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(75),unique=True)
    password = db.Column(db.String(75))

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

#----------------------------------------------------------------------------------------

if not path.exists(DB_NAME):
    db.create_all(app=app)
    print("Database Created")


#--------------------------------------------------------------------------------------
#@app.route("/")
@app.route("/login", methods=['GET','POST'])
def login():
 if request.method == 'POST':
  username = request.form.get("username")
  password = request.form.get("password")

  user = User.query.filter_by(username=username).first()
  if user:
   if check_password_hash(user.password,password):
    flash("logged in", category="success")
    login_user(user,remember=True)
    return redirect('/home')
   else :
    flash("wrong password", category="error")
  else :
   flash("wrong password", category="error")

 return render_template("login.html",user=current_user)

@app.route("/sign-up", methods=['GET','POST'])
def sign_up():
 if request.method == 'POST':
  username = request.form.get("username")
  password1 = request.form.get("password1")
  password2 = request.form.get("password2")

  username_exists = User.query.filter_by(username=username).first()

  if username_exists:
   flash("username already in use",category="error")
  elif password1 != password2 :
   flash("wrong password",category="error")
  if len(username) < 4 :
   flash("username too short",category="error")
  if len(password1) < 6 :
   flash("password too short",category="error")
  else:
   new_user = User(username=username,password=generate_password_hash(password2,method='sha256'))
   db.session.add(new_user)
   db.session.commit()
   login_user(new_user,remember=True)
   flash("user created")
   return redirect('/home')

 return render_template("signup.html",user=current_user)

@app.route("/logout")
@login_required
def logout():
 logout_user()
 return redirect('/')



#------------------------------------------------------------------------------------------------------------

@app.route("/")
@app.route("/home")
@login_required
def home():
    tasks = Task.query.filter_by(user=current_user.username)
    return render_template("home.html",user=current_user,tasks=tasks)

@login_required
@app.route("/refresh-home")
def refresh():
    data = []
    tasks = Task.query.filter_by(user=current_user.username)
    for task in tasks:
       data.append([task.id,task.topic,task.text,task.user,task.completed])
    return jsonify({"user":current_user.username,"data":data})

@login_required
@app.route("/add-task",methods=['GET','POST'])
def add_task():
   if request.method == "POST":
      f = request.files['file']
      topic = request.form.get("title")
      text = request.form.get("text")
      category = request.form.get("category")
      if text and category and topic :
         new_task = Task(topic=topic,text=text,category=category,user=current_user.username)
         db.session.add(new_task)
         db.session.commit()
         if f.filename :
            new_img = Image(task_id=new_task.id,user=current_user.username,url="")
            db.session.add(new_img)
            db.session.commit()
            split = f.filename.split(".")
            f.filename = f"{current_user.username}-{new_task.id}-{new_img.id}.{split[len(split)-1]}"
            f.filename = f.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),f"static/imgs/{f.filename}")
            f.save(f.filename )
            db.session.delete(new_img)
            new_img.url = f"imgs/{current_user.username}-{new_task.id}-{new_img.id}.{split[len(split)-1]}"
            db.session.add(new_img)
            db.session.commit()
         return redirect("/home")
   return render_template("addtask.html",user=current_user)

@login_required
@app.route("/delete-task/<taskid>",methods=['GET','POST'])
def delete_task(taskid):
   user_exists = User.query.filter_by(username = current_user.username).first()
   task_exists = Task.query.filter_by(id = taskid).first()
   img_exists = Image.query.filter_by(task_id = task_exists.id,user=current_user.username)
   if user_exists and task_exists :
       if user_exists.username == task_exists.user :
          db.session.delete(task_exists)
          if img_exists:
            for img in img_exists:
                abs_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)),f"static/{img.url}")
                db.session.delete(img)
                os.remove(abs_path)
                print(abs_path)
          db.session.commit()
          return jsonify({"key":"error"})
   return jsonify({"key":"error"})

@login_required
@app.route("/task/<taskid>",methods=['GET','POST'])
def edit_task(taskid):
   user_exists = User.query.filter_by(username = current_user.username).first()
   task_exists = Task.query.filter_by(id = taskid).first()
   img_exists = Image.query.filter_by(task_id = task_exists.id,user=current_user.username)

   if request.method == "POST":
      topic = request.form.get("title")
      text = request.form.get("text")
      f = request.files['file']
      print(topic,text,f.filename)
      if text and topic :
         task_exists.topic = topic
         task_exists.text = text
         db.session.commit()
         if f.filename :
            new_img = Image(task_id=task_exists.id,user=current_user.username,url="")
            db.session.add(new_img)
            db.session.commit()
            split = f.filename.split(".")
            f.filename = f"{current_user.username}-{task_exists.id}-{new_img.id}.{split[len(split)-1]}"
            f.filename = f.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),f"static/imgs/{f.filename}")         
            f.save(f.filename)
            print(f.filename)
            db.session.delete(new_img)
            new_img.url = f"imgs/{current_user.username}-{task_exists.id}-{new_img.id}.{split[len(split)-1]}"
            db.session.add(new_img)
            db.session.commit()
      return redirect(f'/task/{taskid}')

   if request.method == "GET":
      if user_exists and task_exists :
         if user_exists.username == task_exists.user :
             image_data = []
             for img in img_exists:
                image_data.append([img.id,img.url])
             print("sent",image_data)
             return render_template("task.html",user=current_user,task=task_exists,images=image_data)

      #return redirect(f'/task/{taskid}')


@login_required
@app.route("/delete-img/<taskid>/<img_id>",methods=['GET','POST'])
def delete_img(taskid,img_id):
   user_exists = User.query.filter_by(username = current_user.username).first()
   task_exists = Task.query.filter_by(id = taskid).first()
   img_exists = Image.query.filter_by(task_id = task_exists.id,user=current_user.username,id=img_id).first()
   if user_exists and task_exists :
       if user_exists.username == task_exists.user :
          if img_exists:
                abs_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)),f"static/{img_exists.url}")
                db.session.delete(img_exists)
                os.remove(abs_path)
                print(abs_path)
                db.session.commit()

   return redirect(f"/task/{taskid}")

#------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
    app.run(debug=False,host='0.0.0.0',port=6900)
