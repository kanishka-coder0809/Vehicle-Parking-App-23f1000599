from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Admin(db.Model, UserMixin):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
    def get_id(self):
        return self.email

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer , primary_key = True , autoincrement=True)
    name = db.Column(db.String  , nullable = False)
    email = db.Column(db.String , unique =True , nullable=False)
    password = db.Column(db.String , nullable= False)
    phone = db.Column(db.String , nullable = False)
    city = db.Column(db.String , nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    reserved_parking_spots = db.relationship("ReservedParkingSpot" , backref="user")
    def get_id(self):
        return self.email

class ParkingLot(db.Model):
    __tablename__ = "Parking_Lot"
    id = db.Column(db.Integer , primary_key = True , autoincrement=True)
    prime_location_name = db.Column(db.String, nullable = False)
    price = db.Column(db.Integer, nullable = False) #####
    address = db.Column(db.String, nullable = False)
    city = db.Column(db.String , nullable = False)
    pin_code = db.Column(db.Integer, nullable = False)
    maximum_number_of_spots = db.Column(db.Integer, nullable = False)
    spots = db.relationship("ParkingSpot", backref = "Parking_Lot")
    reserved_parking_spot = db.relationship("ReservedParkingSpot" , backref="Parking_Lot")

class ParkingSpot(db.Model):
    __tablename__ = "Parking_Spot"
    id = db.Column(db.Integer , primary_key = True , autoincrement=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("Parking_Lot.id"), nullable = False)
    status = db.Column(db.String, nullable = False) #how can we add O-Occupied/A-Available here
    reserved_parking_spot = db.relationship("ReservedParkingSpot" , backref="Parking_Spot")

class ReservedParkingSpot(db.Model):
    __tablename__ = "Reserved_Parking_Spot"
    id = db.Column(db.Integer , primary_key = True , autoincrement=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("Parking_Spot.id"), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    lot_id = db.Column(db.Integer, db.ForeignKey('Parking_Lot.id'), nullable=False)
    parking_timestamp = db.Column(db.String, nullable = False)
    leaving_timestamp = db.Column(db.String, nullable = False)
    vehicle_number = db.Column(db.String, nullable = False)
    parkingCost_unitTime = db.Column(db.Integer, nullable = False) ####