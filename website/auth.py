from flask import Blueprint,render_template,url_for,redirect,request,flash
from flask_login import login_user,logout_user,login_required,current_user
from .models import User
from .import db
from werkzeug.security import generate_password_hash,check_password_hash
auth = Blueprint("auth",__name__)

@auth.route("/login", methods=['GET','POST'])
def login():
 if request.method == 'POST':
  username = request.form.get("username")
  password = request.form.get("password")

  user = User.query.filter_by(username=username).first()
  if user:
   if check_password_hash(user.password,password):
    flash("logged in", category="success")
    login_user(user,remember=True)
    return redirect(url_for('views.home'))
   else :
    flash("wrong password", category="error")
  else :
   flash("wrong password", category="error")

 return render_template("login.html",user=current_user)

@auth.route("/sign-up", methods=['GET','POST'])
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
   return redirect(url_for('views.home'))

 return render_template("signup.html",user=current_user)

@auth.route("/logout")
@login_required
def logout():
 logout_user()
 return redirect(url_for("views.home"))

