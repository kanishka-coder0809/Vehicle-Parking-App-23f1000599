from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Coupon(db.Model):
    __tablename__ = "Coupon"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    discount_type = db.Column(db.String(16), nullable=False)  # 'flat' or 'percentage'
    discount_value = db.Column(db.Float, nullable=False)
    min_amount = db.Column(db.Float, nullable=False, default=0)
    max_discount = db.Column(db.Float, nullable=True)
    expiry_date = db.Column(db.String, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, nullable=False, default=0)
    usage_limit_per_user = db.Column(db.Integer, nullable=True)
    applicable_on = db.Column(db.String(32), nullable=False, default='booking')  # booking/subscription/location
    is_active = db.Column(db.Boolean, nullable=False, default=True)

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
    profile_image = db.Column(db.String, nullable=True, default="default.png")
    cover_photo = db.Column(db.String, nullable=True)
    date_of_birth = db.Column(db.String, nullable=True)
    gender = db.Column(db.String, nullable=True)
    bio = db.Column(db.String(240), nullable=True)
    full_address = db.Column(db.String, nullable=True)
    state = db.Column(db.String, nullable=True)
    landmark = db.Column(db.String, nullable=True)
    vehicle_type = db.Column(db.String, nullable=True)
    vehicle_number = db.Column(db.String, nullable=True)
    preferred_parking_type = db.Column(db.String, nullable=True)
    preferred_location = db.Column(db.String, nullable=True)
    time_preference = db.Column(db.String, nullable=True)
    alternate_phone = db.Column(db.String, nullable=True)
    secondary_email = db.Column(db.String, nullable=True)
    wallet_balance = db.Column(db.Float, nullable=False, default=0)
    reserved_parking_spots = db.relationship("ReservedParkingSpot" , backref="user")
    parking_reviews = db.relationship("ParkingLotReview", backref="review_user")
    favorite_lots = db.relationship("FavoriteParkingLot", backref="favorite_user")
    notifications = db.relationship("NotificationLog", backref="notification_user")
    subscriptions = db.relationship("MonthlySubscription", backref="subscription_user")
    availability_alerts = db.relationship("SpotAvailabilityAlert", backref="alert_user")
    wallet_transactions = db.relationship("WalletTransaction", backref="wallet_user")
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
    reviews = db.relationship("ParkingLotReview", backref="review_lot")
    favorites = db.relationship("FavoriteParkingLot", backref="favorite_lot")

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
    planned_duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    planned_amount = db.Column(db.Float, nullable=True)
    billed_amount = db.Column(db.Float, nullable=True)
    refund_amount = db.Column(db.Float, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    reminder_sent = db.Column(db.Boolean, nullable=False, default=False)


class ParkingLotReview(db.Model):
    __tablename__ = "Parking_Lot_Review"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("Parking_Lot.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String, nullable=True)
    created_at = db.Column(db.String, nullable=False)
    __table_args__ = (db.UniqueConstraint("lot_id", "user_id", name="unique_user_lot_review"),)


class FavoriteParkingLot(db.Model):
    __tablename__ = "Favorite_Parking_Lot"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("Parking_Lot.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("lot_id", "user_id", name="unique_user_lot_favorite"),)


class NotificationLog(db.Model):
    __tablename__ = "Notification_Log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    channel = db.Column(db.String, nullable=False)  # email/sms
    subject = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="queued")
    created_at = db.Column(db.String, nullable=False)


class SpotAvailabilityAlert(db.Model):
    __tablename__ = "Spot_Availability_Alert"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey("Parking_Lot.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.String, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "lot_id", name="unique_user_lot_alert"),)


class MonthlySubscription(db.Model):
    __tablename__ = "Monthly_Subscription"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tier = db.Column(db.String, nullable=False)  # standard/premium
    monthly_fee = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.String, nullable=False)
    end_date = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    auto_book_enabled = db.Column(db.Boolean, nullable=False, default=False)
    preferred_lot_id = db.Column(db.Integer, db.ForeignKey("Parking_Lot.id"), nullable=True)


class WalletTransaction(db.Model):
    __tablename__ = "Wallet_Transaction"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    transaction_type = db.Column(db.String, nullable=False)  # credit/debit/refund/withdrawal
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.String, nullable=False)