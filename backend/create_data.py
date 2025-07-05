from .models import db, Admin, ParkingLot

if db.session.query(Admin).count() == 0:
    A = Admin(name = "admin" , email="admin@myapp.com" , password = "pass")
    db.session.add(A)
    db.session.commit()

if db.session.query(ParkingLot).count() == 0:
    P1 = ParkingLot(prime_location_name="Ambience Mall", price=800, address="DLF Phase 3, Sector-24, Gurgaon", pin_code=122002, maximum_number_of_spots=250)
    db.session.add(P1)
    P2 = ParkingLot(prime_location_name="Golf Course", price=600, address="Sector-38, Noida, Gautam Buddh Nagar", pin_code=201303, maximum_number_of_spots=100)
    db.session.add(P2)
    P3 = ParkingLot(prime_location_name="Janam Bhoomi", price=250, address="Near Deeg Gate Chauraha, Mathura", pin_code=281004, maximum_number_of_spots=150)
    db.session.add(P3)
    P4 = ParkingLot(prime_location_name="Sanjay Palace", price=100, address="Civil Lines, Agra", pin_code=282002, maximum_number_of_spots=150)
    db.session.add(P4)
    db.session.commit()