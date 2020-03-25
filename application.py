from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import *
import requests

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'clavesecreta'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == 'GET':
        return render_template("login.html")

    if request.method == 'POST':
         # Get form information.
        name = request.form.get("username")
        psw = request.form.get("password")

        # Make sure the user and password are correct.
        user = Usuario.query.filter_by(username=name, password=psw).first()
        if not user:
            return render_template("login.html", message="Invalid username or password ")
        login_user(user)
        return redirect(url_for('send'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    if request.method == 'POST':
            # Get form information.
        username = request.form.get("username")
        psw = request.form.get("password")
       
        # Make sure the user exists.
        user = Usuario.query.filter_by(username=username).first()
        if user:
            return render_template("error.html", message="Username already exists")
        nuevo = Usuario(username=username, password=psw)
        db.session.add(nuevo)   
        db.session.commit()
        login_user(nuevo)
        return redirect(url_for('send'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    if request.method == 'POST':
        phone = request.form.get("phone")
        body = request.form.get("mensaje")
        url = 'https://eu108.chat-api.com/instance110344/message?token=1aev7uljuh7eyscw'
        data = ({"phone": phone, "body": body})
        res = requests.post(url, json=data)
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        print(data)
    return render_template("send.html")