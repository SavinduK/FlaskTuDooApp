from flask import Blueprint,render_template,request,flash,redirect,url_for,jsonify
from flask_login import current_user, login_required
from .models import User,Task,Image
from . import db
from flask_wtf.csrf import CSRFProtect
from fileinput import filename
import sys
import os
from werkzeug.utils import secure_filename

views = Blueprint("views",__name__)

@views.route("/")
@views.route("/home")
@login_required
def home():
    tasks = Task.query.filter_by(user=current_user.username)
    return render_template("home.html",user=current_user,tasks=tasks)

@login_required
@views.route("/refresh-home")
def refresh():
    data = []
    tasks = Task.query.filter_by(user=current_user.username)
    for task in tasks:
       data.append([task.id,task.topic,task.text,task.user,task.completed])
    return jsonify({"user":current_user.username,"data":data})

@login_required
@views.route("/add-task",methods=['GET','POST'])
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
            f.filename = f"website/static/imgs/{f.filename}"
            f.save(f.filename )
            db.session.delete(new_img)
            new_img.url = f"imgs/{current_user.username}-{new_task.id}-{new_img.id}.{split[len(split)-1]}"
            db.session.add(new_img)
            db.session.commit()
         return redirect("/home")
   return render_template("addtask.html",user=current_user)

@login_required
@views.route("/delete-task/<taskid>",methods=['GET','POST'])
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
@views.route("/task/<taskid>",methods=['GET','POST'])
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
         print("c0")
         task_exists.topic = topic
         task_exists.text = text
         db.session.commit()
         print("c1")
         if f.filename :
            print("c3")
            new_img = Image(task_id=task_exists.id,user=current_user.username,url="")
            db.session.add(new_img)
            db.session.commit()
            split = f.filename.split(".")
            f.filename = f"{current_user.username}-{task_exists.id}-{new_img.id}.{split[len(split)-1]}"
            f.filename = f"website/static/imgs/{f.filename}"
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
@views.route("/delete-img/<taskid>/<img_id>",methods=['GET','POST'])
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