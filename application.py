import os
import csv
from os import remove
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import *
from config import *
import requests
from decouple import config as config_decouple
from datauri import DataURI
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict


def create_app(enviroment):
    app = Flask(__name__)

    app.config.from_object(enviroment)

    with app.app_context():
        db.init_app(app)
        db.create_all()

    return app

enviroment = config['development']
if config_decouple('PRODUCTION', default=False):
    enviroment = config['production']

app = create_app(enviroment)

app.config["SECRET_KEY"] = 'clavesecreta'

login_manager = LoginManager()
login_manager.init_app(app)

uploads_dir = os.path.join(app.root_path, 'uploads')
if  not os.path.isdir(str(uploads_dir)):
    os.mkdir(uploads_dir)

numeros = []

iconos = []
f = open("iconos.csv")
reader = csv.reader(f, delimiter=";")
for row in reader:
    iconos.append(row[0])

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))



@app.route("/")
def index():
    if current_user.is_authenticated:
        usuarios = Usuario.query.all()
        lineas = Linea.query.all()
        if current_user.is_admin():
            return render_template("admin.html", usuarios=usuarios, lineas=lineas)
        else:
            return redirect(url_for('send'))
    else:
        return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == 'GET':
        return render_template("login.html")

    if request.method == 'POST':
         # Get form information.
        name = request.form.get("username")
        psw = request.form.get("password")

        # Make sure the user and password are correct.
        user = Usuario.query.filter_by(username=name).first()
        if not user:
            return render_template("login.html", message="Invalid username")
        if not check_password_hash(user.password_hash, psw):
            return render_template("login.html", message="Invalid password ")
        login_user(user)
        return redirect(url_for('send'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    if request.method == 'POST':
            # Get form information.
        name = request.form.get("name")
        username = request.form.get("username")
        psw = request.form.get("password")
       
        # Make sure the user exists.
        user = Usuario.query.filter_by(username=username).first()
        if user:
            return render_template("error.html", message="Username already exists")
        
        nuevo = Usuario(name=name.capitalize(), username=username)
        nuevo.password_hash = generate_password_hash(psw)
        nuevo.admin = False
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
        if phone not in numeros:
            numeros.append(phone)
        archivo = request.files["archivo"]
        if archivo.filename:
            url = 'https://eu108.chat-api.com/instance110344/sendFile?token=1aev7uljuh7eyscw'
            archivo.save(os.path.join(uploads_dir, secure_filename(archivo.filename)))
            mensaje = request.form.get("mensaje")
            ruta = os.path.join(uploads_dir, secure_filename(archivo.filename))
            body = DataURI.from_file(str(ruta))
            data = ({"phone": phone, "body": body, "filename": archivo.filename, "caption": mensaje })
        elif not archivo:
            body = request.form.get("mensaje")
            url = 'https://eu108.chat-api.com/instance110344/message?token=1aev7uljuh7eyscw'
            data = ({"phone": phone, "body": body})
        res = requests.post(url, json=data, timeout=2000)
        if archivo:
            remove(str(os.path.join(uploads_dir, secure_filename(archivo.filename))))
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        print(data)
        return render_template("send.html", message="Enviado con exito", numeros=numeros, iconos=iconos)
    if request.method == 'GET':
        return render_template("send.html", numeros=numeros, iconos=iconos)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    
    if request.method == 'GET':
        if current_user.is_admin():
            usuarios = Usuario.query.all()
            lineas = Linea.query.all()
            return render_template("admin.html", usuarios=usuarios, lineas=lineas)
        else:
            return redirect(url_for('send'))
    if request.method == 'POST':
        formulario = request.get_json()
        user_id = Usuario.query.filter_by(username=formulario["usuario"]).first()
        linea_id = Linea.query.filter(Linea.name.in_(formulario['instancias'])).all()
        for inst in linea_id:
            check = Asignacion.query.filter_by(user_id=user_id.id).filter_by(linea_id=inst.id).first()
            if check:
                continue
            nueva = Asignacion(user_id=user_id.id, linea_id=inst.id)
            db.session.add(nueva)   
        db.session.commit() 
        return redirect(url_for('index'))

@app.route("/linea", methods=["GET", "POST"])
@login_required
def linea():
    if current_user.is_admin():
        if request.method == 'GET':
            return render_template("linea.html")

        if request.method == 'POST':
                # Get form information.
            name = request.form.get("name")
            apiurl = request.form.get("apiurl")
            token = request.form.get("token")
            nueva = Linea(name=name, api_url=apiurl, token=token)
            db.session.add(nueva)   
            db.session.commit()
            return render_template("linea.html", message="Agregada con exito")
    else:
        return redirect(url_for('send'))