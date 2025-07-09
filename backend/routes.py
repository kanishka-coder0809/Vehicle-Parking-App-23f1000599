from app import app
from flask import render_template, request, redirect
from .models import db, Admin, User
from flask_login import login_user, login_required, current_user

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET": 
        return render_template("register.html")
    elif request.method == "POST":
        u_name = request.form.get("name")
        u_email = request.form.get("email")
        u_password = request.form.get("password")
        u_phone = request.form.get("phone")
        user = db.session.query(User).filter_by(email = u_email).first()
        if user:
            return "E-mail Already Exist"
        else:
            new_user = User(name = u_name, email = u_email, password = u_password, phone = u_phone)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")

@app.route("/login", methods =["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        l_email = request.form.get("email")
        l_password = request.form.get("password")

        login = db.session.query(Admin).filter_by(email=l_email).first() or db.session.query(User).filter_by(email=l_email).first()

        if login:
            if login.password == l_password:
                if isinstance(login, Admin):
                    login_user(login)
                    return redirect(f"/admin/dashboard?login_id={login.id}")
                elif isinstance(login, User):
                    login_user(login)
                    return redirect(f"/user/dashboard?login_id={login.id}")
            else:
                return "Incorrect Password"
        else:
            return "E-mail doesn't exist"

@app.route("/admin/dashboard")
@login_required  
def admin_dash():
    return render_template("/admin/dashboard.html")

@app.route("/user/dashboard")
@login_required
def user_dash():
    return render_template("/user/dashboard.html", curr_user = current_user)

@app.route("/user/stats")
@login_required
def user_stats():
    return f"Welcome to {current_user.name} stats."
