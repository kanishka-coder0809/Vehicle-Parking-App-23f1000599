from app import app
from flask import render_template, request, redirect, flash
from .models import db, Admin, User, ParkingLot, ParkingSpot, ReservedParkingSpot
from flask_login import login_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from datetime import datetime

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
    all_users = db.session.query(User).all()

    # Check and create missing parking spots for each lot
    for lot in all_par:
        existing_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        if existing_spots < lot.maximum_number_of_spots:
            for _ in range(existing_spots + 1, lot.maximum_number_of_spots + 1):
                new_spot = ParkingSpot(lot_id=lot.id, status="A")  # A = Available
                db.session.add(new_spot)
            db.session.commit()
    return render_template("/admin/dashboard.html", all_par = all_par, all_users = all_users)

@app.route("/user/dashboard")
@login_required
def user_dash():
    # Fetch all lots with at least one available spot
    all_par = db.session.query(ParkingLot).join(ParkingSpot).filter(ParkingSpot.status == 'A').distinct().all()
    return render_template("/user/dashboard.html", curr_user=current_user, all_par=all_par)

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
        par_max = int(request.form.get("maximum_number_of_spots")) #ensure that it is a integer
        parking = db.session.query(ParkingLot).filter_by(prime_location_name=par_name).first()
        if parking:
            # Get current number of ParkingSpots
            current_spots = db.session.query(ParkingSpot).filter_by(lot_id=parking.id).all()
            current_count = len(current_spots)

            # Update ParkingLot fields
            parking.prime_location_name = par_name
            parking.price = par_price
            parking.address = par_add
            parking.city = par_city
            parking.pin_code = par_pin
            parking.maximum_number_of_spots = par_max
            
            # Handle difference in spot count
            if par_max > current_count:
                # Add new spots
                for _ in range(current_count + 1, par_max + 1):
                    new_spot = ParkingSpot(lot_id=parking.id, status='A')
                    db.session.add(new_spot)
            elif par_max < current_count:
                # Remove extra spots (Only remove available ones to avoid deleting reserved)
                removable_spots = [spot for spot in current_spots if spot.status == 'A']
                for spot in removable_spots[:current_count - par_max]:
                    db.session.delete(spot)
            db.session.commit()
            return redirect("/admin/dashboard")
        else:
            return "Parking Lot doesn't exist"

@app.route("/booking", methods=["POST"])
@login_required
def booking():
    lot_id = request.form.get("lot_id")
    lot = db.session.query(ParkingLot).filter_by(id=lot_id).first()

    if not lot:
        return "Invalid Parking Lot", 400

    # Find first available spot in the lot
    available_spot = db.session.query(ParkingSpot).filter_by(lot_id=lot_id, status='A').first()

    if not available_spot:
        flash("No available parking spots in this lot.", "danger")
        return redirect("/user/dashboard")

    # Mark spot as occupied
    available_spot.status = 'O'

    # Create reservation
    now = datetime.now()
    reservation = ReservedParkingSpot(spot_id=available_spot.id, lot_id=lot.id, user_id=current_user.id, parking_timestamp=now.strftime('%Y-%m-%d %H:%M:%S'), leaving_timestamp="Not yet left",  parkingCost_unitTime=lot.price)
    db.session.add(reservation)
    db.session.commit()
    flash("Parking Spot Booked Successfully!", "success")
    return redirect("/user/dashboard")