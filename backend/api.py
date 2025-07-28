from flask_restful import Resource, Api
from .models import *

api = Api()

class ParkingLotResource(Resource):
    def get(self):
        all_parkings = db.session.query(ParkingLot).all()
        parkings = []
        for parking in  all_parkings:
            parkings.append({"parking_lot_id" : parking.id, "parking_lot_name" : parking.prime_location_name, "parking_lot_price" : parking.price, "parking_lot_address" : parking.address, "parking_lot_city" : parking.city, "parking_lot_pincode" : parking.pin_code, "parking_lot_max_spots" : parking.maximum_number_of_spots})
        return parkings
    
api.add_resource(ParkingLotResource, "/api/parkingLot")

# class ParkingSpotResource(Resource):


# class BookingResource(Resource):