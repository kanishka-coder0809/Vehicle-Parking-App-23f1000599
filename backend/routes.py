from app import app
from flask import render_template, request, redirect, flash
from .models import db, Admin, User, ParkingLot, ParkingSpot, ReservedParkingSpot
from flask_login import login_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt

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

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    # Check and create missing parking spots for each lot
    for lot in all_par:
        existing_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        if existing_spots < lot.maximum_number_of_spots:
            for _ in range(existing_spots + 1, lot.maximum_number_of_spots + 1):
                new_spot = ParkingSpot(lot_id=lot.id, status="A")  # A = Available
                db.session.add(new_spot)
            db.session.commit()
    return render_template("/admin/dashboard.html", all_par = all_par, all_users = all_users, user_histories= user_histories)


@app.route("/admin/search", methods = ["GET", "POST"])
def admin_search():
    all_users = db.session.query(User).all()

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    if request.method == "GET":
        return render_template("/admin/search.html")
    elif request.method == "POST":
        type = request.form.get("searchby")
        query = request.form.get("search_query")
        result = []
        if type == "user":
            result = db.session.query(User).filter(User.name.ilike(f"%{query}%")).all()
        elif type == "parking":
            result = db.session.query(ParkingLot).filter(ParkingLot.prime_location_name.ilike(f"%{query}%")).all()
        return render_template("/admin/search.html", results = result, type = type, user_histories= user_histories, request = request)
    
@app.route("/admin/summary")
def admin_summary():
    if request.method == "GET":
        parkings = db.session.query(ParkingLot).all()
        park_names = []
        book_count = []
        for parking in parkings:
            park_names.append(parking.prime_location_name)
            book_count.append(len(parking.reserved_parking_spot))
        plt.barh(y = park_names, width = book_count)
        plt.savefig("./static/admin/parkinglot_booking_count.png", bbox_inches='tight', pad_inches=0.5)
        plt.close()
        return render_template("/admin/summary.html")

@app.route("/user/dashboard")
@login_required
def user_dash():
    # Fetch all lots with at least one available spot
    all_par = db.session.query(ParkingLot).join(ParkingSpot).filter(ParkingSpot.status == 'A').distinct().all()
    #fetch registered users
    booking_history = db.session.query(ReservedParkingSpot).filter_by(user_id=current_user.id).all()
    # Add duration for released spots
    for booking in booking_history:
        if booking.leaving_timestamp != "Not yet left":
            start_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(booking.leaving_timestamp, "%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            booking.duration = str(duration)  # This will be like '0:45:00' (HH:MM:SS)
        else:
            booking.duration = "Ongoing"
    return render_template("/user/dashboard.html", curr_user=current_user, all_par=all_par, booking_history = booking_history)

@app.route("/user/search", methods = ["GET", "POST"])
def user_search():
    all_users = db.session.query(User).all()

    user_histories = {
        user.id: ReservedParkingSpot.query.filter_by(user_id=user.id).all()
        for user in all_users
    }

    if request.method == "GET":
        return render_template("/user/search.html")
    elif request.method == "POST":
        type = request.form.get("searchby")
        query = request.form.get("search_query")
        result = []
        if type == "name":
            result = db.session.query(ParkingLot).filter(ParkingLot.prime_location_name.ilike(f"%{query}%")).all()
        elif type == "address":
            result = db.session.query(ParkingLot).filter(ParkingLot.address.ilike(f"%{query}%")).all()
        elif type == "city":
            result = db.session.query(ParkingLot).filter(ParkingLot.city.ilike(f"%{query}%")).all()
        if type == "pincode":
            result = db.session.query(ParkingLot).filter(ParkingLot.pin_code.ilike(f"%{query}%")).all()
        return render_template("/user/search.html", results = result, type = type, user_histories= user_histories, request = request)

@app.route('/user/summary')
@login_required
def user_summary():
    from datetime import datetime
    from collections import defaultdict
    import matplotlib.pyplot as plt

    # Fetch all bookings for current user
    bookings = ReservedParkingSpot.query.filter_by(user_id=current_user.id).all()

    summary_data = []
    bookings_per_day = defaultdict(int)  # for line chart

    for booking in bookings:
        if booking.leaving_timestamp != "Not yet left":
            in_time = datetime.strptime(booking.parking_timestamp, "%Y-%m-%d %H:%M:%S")
            out_time = datetime.strptime(booking.leaving_timestamp, "%Y-%m-%d %H:%M:%S")
            duration = out_time - in_time

            total_cost = booking.total_cost or round((duration.total_seconds() / 3600) * booking.parkingCost_unitTime, 2)

            summary_data.append({
                'spot_id': booking.spot_id,
                'lot_name': booking.Parking_Lot.prime_location_name,
                'in_time': booking.parking_timestamp,
                'out_time': booking.leaving_timestamp,
                'duration': str(duration),
                'vehicle_number': booking.vehicle_number,
                'cost': f"₹{total_cost:.2f}"
            })

            date_only = in_time.date().isoformat()  # Extract YYYY-MM-DD
            bookings_per_day[date_only] += 1

    # Sort the bookings by date
    sorted_dates = sorted(bookings_per_day)
    booking_counts = [bookings_per_day[date] for date in sorted_dates]

    # Plot line chart
    plt.figure(figsize=(8, 4))
    plt.plot(sorted_dates, booking_counts, marker='o', linestyle='-', color='blue')
    plt.xlabel("Date")
    plt.ylabel("No. of Bookings")
    plt.title("Your Parking Bookings Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save chart to static folder
    chart_path = "./static/user/user_booking_trend.png"
    plt.savefig(chart_path, bbox_inches='tight', pad_inches=0.5)
    plt.close()

    return render_template('/user/summary.html', summary_data=summary_data, chart_path=chart_path)


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
    vehicle_no = request.form.get("vehicle_number")

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
    reservation = ReservedParkingSpot(spot_id=available_spot.id, lot_id=lot.id, user_id=current_user.id, parking_timestamp=now.strftime('%Y-%m-%d %H:%M:%S'), leaving_timestamp="Not yet left",  parkingCost_unitTime=lot.price, vehicle_number=vehicle_no)
    db.session.add(reservation)
    db.session.commit()
    flash("Parking Spot Booked Successfully!", "success")
    return redirect("/user/dashboard")

@app.route("/release/<int:booking_id>", methods=["POST"])
@login_required
def release_spot(booking_id):
    reservation = db.session.query(ReservedParkingSpot).filter_by(id=booking_id, user_id=current_user.id).first()
    
    if reservation and reservation.leaving_timestamp == "Not yet left":
        reservation.leaving_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Make the spot available again
        spot = db.session.query(ParkingSpot).filter_by(id=reservation.spot_id).first()
        if spot:
            spot.status = 'A'
        
        db.session.commit()
        flash("Spot released successfully.", "success")
    else:
        flash("Invalid or already released booking.", "danger")
    
    return redirect("/user/dashboard")
