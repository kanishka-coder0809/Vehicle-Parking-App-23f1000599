

# Clean imports at the top
from flask_restful import Resource, Api, request
from .models import db, Coupon, ParkingLot

# Create API instance (only once)
api = Api()


class CouponResource(Resource):
    def get(self):
        coupons = db.session.query(Coupon).all()
        result = []
        for c in coupons:
            result.append({
                "id": c.id,
                "code": c.code,
                "discount_type": c.discount_type,
                "discount_value": c.discount_value,
                "min_amount": c.min_amount,
                "max_discount": c.max_discount,
                "expiry_date": c.expiry_date,
                "usage_limit": c.usage_limit,
                "used_count": c.used_count,
                "usage_limit_per_user": c.usage_limit_per_user,
                "applicable_on": c.applicable_on,
                "is_active": c.is_active,
            })
        return result

    def post(self):
        data = request.get_json(force=True)
        code = data.get("code")
        if not code:
            return {"message": "Coupon code required."}, 400
        if db.session.query(Coupon).filter_by(code=code).first():
            return {"message": "Coupon code already exists."}, 409
        coupon = Coupon(
            code=code,
            discount_type=data.get("discount_type"),
            discount_value=data.get("discount_value"),
            min_amount=data.get("min_amount", 0),
            max_discount=data.get("max_discount"),
            expiry_date=data.get("expiry_date"),
            usage_limit=data.get("usage_limit"),
            used_count=0,
            usage_limit_per_user=data.get("usage_limit_per_user"),
            applicable_on=data.get("applicable_on", "booking"),
            is_active=data.get("is_active", True),
        )
        db.session.add(coupon)
        db.session.commit()
        return {"message": "Coupon created."}, 201

    def put(self, id):
        coupon = db.session.query(Coupon).filter_by(id=id).first()
        if not coupon:
            return {"message": "Coupon not found."}, 404
        data = request.get_json(force=True)
        for field in [
            "code", "discount_type", "discount_value", "min_amount", "max_discount",
            "expiry_date", "usage_limit", "usage_limit_per_user", "applicable_on", "is_active"
        ]:
            if field in data:
                setattr(coupon, field, data[field])
        db.session.commit()
        return {"message": "Coupon updated."}

    def delete(self, id):
        coupon = db.session.query(Coupon).filter_by(id=id).first()
        if not coupon:
            return {"message": "Coupon not found."}, 404
        db.session.delete(coupon)
        db.session.commit()
        return {"message": "Coupon deleted."}



# Register resources after class definitions
api.add_resource(CouponResource, "/api/coupons", "/api/coupons/<int:id>")


class ParkingLotResource(Resource):
    def get(self):
        all_parkings = db.session.query(ParkingLot).all()
        parkings = []
        for parking in all_parkings:
            parkings.append({
                "parking_lot_id": parking.id,
                "parking_lot_name": parking.prime_location_name,
                "parking_lot_price": parking.price,
                "parking_lot_address": parking.address,
                "parking_lot_city": parking.city,
                "parking_lot_pincode": parking.pin_code,
                "parking_lot_max_spots": parking.maximum_number_of_spots
            })
        return parkings

    def post(self):
        parking_lot_name = request.form.get("parking_lot_name")
        parking_lot_price = request.form.get("parking_lot_price")
        parking_lot_address = request.form.get("parking_lot_address")
        parking_lot_city = request.form.get("parking_lot_city")
        parking_lot_pincode = request.form.get("parking_lot_pincode")
        parking_lot_max_spots = request.form.get("parking_lot_max_spots")

        parking = db.session.query(ParkingLot).filter_by(prime_location_name=parking_lot_name).first()
        if parking:
            return {"message": "Parking Lot already exist."}, 409

        new_parking = ParkingLot(
            prime_location_name=parking_lot_name,
            price=parking_lot_price,
            address=parking_lot_address,
            city=parking_lot_city,
            pin_code=parking_lot_pincode,
            maximum_number_of_spots=parking_lot_max_spots
        )
        db.session.add(new_parking)
        db.session.commit()
        return {"message": "Parking Lot is created"}

# Register resource after class definition
api.add_resource(ParkingLotResource, "/api/parkingLot")
