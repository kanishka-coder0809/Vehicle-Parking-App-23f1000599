from flask_restful import Resource, Api, request
from .models import *

api = Api()

class ParkingLotResource(Resource):
    def get(self):
        all_parkings = db.session.query(ParkingLot).all()
        parkings = []
        for parking in  all_parkings:
            parkings.append({"parking_lot_id" : parking.id, "parking_lot_name" : parking.prime_location_name, "parking_lot_price" : parking.price, "parking_lot_address" : parking.address, "parking_lot_city" : parking.city, "parking_lot_pincode" : parking.pin_code, "parking_lot_max_spots" : parking.maximum_number_of_spots})
        return parkings
    def post(self):
        parking_lot_name = request.form.get("parking_lot_name")
        parking_lot_price = request.form.get("parking_lot_price")
        parking_lot_address = request.form.get("parking_lot_address")
        parking_lot_city = request.form.get("parking_lot_city")
        parking_lot_pincode = request.form.get("parking_lot_pincode")
        parking_lot_max_spots = request.form.get("parking_lot_max_spots")

        parking = db.session.query(ParkingLot).filter_by(prime_location_name = parking_lot_name).first()
        if parking:
            return {"message" : "Parking Lot already exist."} , 409

        new_parking = ParkingLot(prime_location_name = parking_lot_name, price = parking_lot_price, address = parking_lot_address, city = parking_lot_city, pin_code = parking_lot_pincode, maximum_number_of_spots = parking_lot_max_spots)
        db.session.add(new_parking)
        db.session.commit()
        return {"message" : "Parking Lot is created"}
    
api.add_resource(ParkingLotResource, "/api/parkingLot")
