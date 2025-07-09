#for initializing project

from flask import Flask
from backend.models import db, Admin, User
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vehicle__app_db.sqlite3"
    app.config["SECRET_KEY"] = "thisismayankdhangar"
    db.init_app(app)
    login_manager = LoginManager(app)
    @login_manager.user_loader
    def load_user(id): #taking the id from cookies
        return db.session.query(User).filter_by(id = id).first() or db.session.query(Admin).filter_by(id = id).first()

    app.app_context().push()
    db.create_all()
    return app

app = create_app()

from backend.routes import *
from backend.create_data import *

#the server is running only if we want to run app.py file 
if __name__ == "__main__":
    app.run(debug=True)