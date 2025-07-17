from app import app
from flask import render_template, request, redirect
from .models import db, Admin, User, ParkingLot
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
                    return redirect(f"/admin/dashboard")
                elif isinstance(login, User):
                    login_user(login)
                    return redirect(f"/user/dashboard")
            else:
                return "Incorrect Password"
        else:
            return "E-mail doesn't exist"

@app.route("/admin/dashboard")
@login_required  
def admin_dash():
    all_par = db.session.query(ParkingLot).all()
    return render_template("/admin/dashboard.html", all_par = all_par)

@app.route("/user/dashboard")
@login_required
def user_dash():
    return render_template("/user/dashboard.html", curr_user = current_user)

@app.route("/user/stats")
@login_required
def user_stats():
    return f"Welcome to {current_user.name} stats."

@app.route("/parkingLots", methods=["POST"])
def parkingLot():
    if request.args.get("task") == "create":
        par_name = request.form.get("name")
        par_price = request.form.get("price")
        par_add = request.form.get("address")
        par_city = request.form.get("city")
        par_pin = request.form.get("pincode")
        par_max = request.form.get("maximum_number_of_spots")
        parking = db.session.query(ParkingLot).filter_by(prime_location_name=par_name).first()
        if parking:
            return "Parking Lot Already Exist"
        else:
            new_par = ParkingLot(prime_location_name = par_name, price = par_price, address = par_add, city = par_city, pin_code = par_pin, maximum_number_of_spots = par_max)
            db.session.add(new_par)
            db.session.commit()
            return redirect("/admin/dashboard")
    elif request.args.get("task") == "edit":
        par_name = request.form.get("name")
        par_price = request.form.get("price")
        par_add = request.form.get("address")
        par_city = request.form.get("city")
        par_pin = request.form.get("pincode")
        par_max = request.form.get("maximum_number_of_spots")
        parking = db.session.query(ParkingLot).filter_by(prime_location_name=par_name).first()
        if parking:
            parking.prime_location_name = par_name
            parking.price = par_price
            parking.address = par_add
            parking.city = par_city
            parking.pin_code = par_pin
            parking.maximum_number_of_spots = par_max
            db.session.commit()
            return redirect("/admin/dashboard")
        else:
            return "Category doesn't exist"
