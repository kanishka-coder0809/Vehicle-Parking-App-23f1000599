#for initializing project

from flask import Flask, session, redirect, request, url_for
from backend.models import db, Admin, User
from flask_login import LoginManager
from backend.api import api
from sqlalchemy import text

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vehicle__app_db.sqlite3"
    app.config["SECRET_KEY"] = "thisismayankdhangar"
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = ""
    app.config["MAIL_PASSWORD"] = ""
    app.config["MAIL_DEFAULT_SENDER"] = "noreply@findmyspot.local"
    app.config["MAIL_SUPPRESS_SEND"] = True

    @app.route('/set_language/<lang>')
    def set_language(lang):
        if lang in ['en', 'hi']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('routes.login'))

    db.init_app(app)
    api.init_app(app)
    login_manager = LoginManager(app)

    # Register Blueprint for all routes
    from backend.routes import routes
    app.register_blueprint(routes)

    @login_manager.user_loader
    def load_user(email): #taking the id from cookies
        return db.session.query(User).filter_by(email = email).first() or db.session.query(Admin).filter_by(email = email).first()

    app.app_context().push()
    db.create_all()

    # Lightweight schema upgrades for existing SQLite databases.
    def ensure_column(table_name, column_name, column_sql):
        cols = db.session.execute(text(f"PRAGMA table_info('{table_name}')")).fetchall()
        col_names = {c[1] for c in cols}
        if column_name not in col_names:
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))
            db.session.commit()

    ensure_column("user", "profile_image", "profile_image VARCHAR")
    ensure_column("user", "cover_photo", "cover_photo VARCHAR")
    ensure_column("user", "date_of_birth", "date_of_birth VARCHAR")
    ensure_column("user", "gender", "gender VARCHAR")
    ensure_column("user", "bio", "bio VARCHAR(240)")
    ensure_column("user", "full_address", "full_address VARCHAR")
    ensure_column("user", "state", "state VARCHAR")
    ensure_column("user", "landmark", "landmark VARCHAR")
    ensure_column("user", "vehicle_type", "vehicle_type VARCHAR")
    ensure_column("user", "vehicle_number", "vehicle_number VARCHAR")
    ensure_column("user", "preferred_parking_type", "preferred_parking_type VARCHAR")
    ensure_column("user", "preferred_location", "preferred_location VARCHAR")
    ensure_column("user", "time_preference", "time_preference VARCHAR")
    ensure_column("user", "alternate_phone", "alternate_phone VARCHAR")
    ensure_column("user", "secondary_email", "secondary_email VARCHAR")
    ensure_column("user", "wallet_balance", "wallet_balance FLOAT DEFAULT 0")
    ensure_column("Reserved_Parking_Spot", "reminder_sent", "reminder_sent BOOLEAN DEFAULT 0")
    ensure_column("Reserved_Parking_Spot", "billed_amount", "billed_amount FLOAT")
    ensure_column("Reserved_Parking_Spot", "refund_amount", "refund_amount FLOAT")
    ensure_column("Reserved_Parking_Spot", "planned_duration_minutes", "planned_duration_minutes INTEGER DEFAULT 60")
    ensure_column("Reserved_Parking_Spot", "planned_amount", "planned_amount FLOAT")

    db.session.execute(text("UPDATE user SET wallet_balance = 0 WHERE wallet_balance IS NULL"))
    db.session.commit()

    return app

app = create_app()
app.secret_key = "my_super_secret_key_123"
## Blueprint is now registered above; do not import *
from backend.create_data import *
from backend.api import *

#the server is running only if we want to run app.py file 
if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)