from app import app

@app.route("/")
def index():
    return "hello World"


@app.route("/home")
def home():
    return "welcome to home"

@app.route("/login")
def login():
    return "welcome to login"