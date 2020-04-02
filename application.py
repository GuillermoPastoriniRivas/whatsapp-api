# -*- coding: latin-1 -*-
import os
import csv
import random
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
import sys
import io




def create_app(enviroment):
    app = Flask(__name__)

    app.config.from_object(enviroment)

    with app.app_context():
        db.init_app(app)
        db.create_all()

    return app
nueva_codificacion = 'latin_1'

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding=nueva_codificacion)
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


iconos = []
f = open("iconos.csv")
reader = csv.reader(f, delimiter=";")
for row in reader:
    iconos.append(row[0])

paises = {
    "Argentina":"549",
    "Brasil":"55",
    "Bolivia":"591", 
    "Chile":"56",
    "Colombia":"57", 
    "Ecuador":"593", 
    "Mexico":"52",
    "Perú":"51",
    "Paraguay":"595",
    "Uruguay":"598",
    "Venezuela":"58"
}

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
                return redirect(url_for('admin'))
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
        return redirect(url_for('index'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    if request.method == 'POST':
            # Get form information.
        
        return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    paisuser = paises[current_user.pais]
    numeros = []
    asignaciones = Asignacion.query.filter_by(user_id=current_user.id).all()
    enviados = Enviado.query.filter_by(user=current_user.username).all()
    if enviados:
        for mensaje in enviados:
            if mensaje.numero not in numeros:
                numeros.append(mensaje.numero)
    lineas = []
    for asig in asignaciones:
        agreg = Linea.query.get(asig.linea_id)
        lineas.append(agreg)
    if request.method == 'POST':
        instancia = random.choice(lineas)
        numero = str(request.form.get("phone"))
        prefijo = str(request.form.get("selectorflags"))
        cliente = request.form.get("cliente")
        phone = prefijo + numero
        if cliente:
            body = cliente
            instancias = str(instancia.api_url)
            tokens = str(instancia.token)
            url = f'{instancias}message?token={tokens}'
            data = ({"phone": phone, "body": body})
            res = requests.post(url, json=data, timeout=2000)
            if res.status_code != 200:
                raise Exception("ERROR: API request unsuccessful.")
            nuevo = Enviado(user=current_user.username, linea=instancia.name, numero=numero, prefijo=prefijo, mensaje=body)
            db.session.add(nuevo) 
            db.session.commit() 
        archivo = request.files["archivo"]
        if archivo.filename:
            instancias = str(instancia.api_url)
            tokens = str(instancia.token)
            mensaje = request.form.get("mensaje")
            if mensaje:
                if current_user.mensajeoculto:
                    f = open('mensaje.txt')
                    mensajeoculto = f.read()
                    mensaje = f'''{mensaje}\n\n\n{mensajeoculto}'''
                url = f'{instancias}message?token={tokens}'
                data = ({"phone": phone, "body": mensaje})
                res = requests.post(url, json=data, timeout=2000)
                if res.status_code != 200:
                    raise Exception("ERROR: API request unsuccessful.")
                nuevo = Enviado(user=current_user.username, linea=instancia.name, numero=numero, prefijo=prefijo, mensaje=mensaje)
                db.session.add(nuevo) 
                db.session.commit() 
            url = f'{instancias}sendFile?token={tokens}'
            archivo.save(os.path.join(uploads_dir, secure_filename(archivo.filename)))
            ruta = os.path.join(uploads_dir, secure_filename(archivo.filename))
            body = DataURI.from_file(str(ruta))
            data = ({"phone": phone, "body": body, "filename": archivo.filename })
            nuevo = Enviado(user=current_user.username, linea=instancia.name, numero=numero, prefijo=prefijo, archivo=archivo.filename)
            db.session.add(nuevo) 
            db.session.commit() 
        elif not archivo:
            body = request.form.get("mensaje")
            if current_user.mensajeoculto:
                f = open('mensaje.txt')
                mensajeoculto = f.read()
                body = f'''{body}\n\n\n{mensajeoculto}'''
            instancias = str(instancia.api_url)
            tokens = str(instancia.token)
            url = f'{instancias}message?token={tokens}'
            data = ({"phone": phone, "body": body})
            nuevo = Enviado(user=current_user.username, linea=instancia.name, numero=numero, prefijo=prefijo, mensaje=body)
            db.session.add(nuevo) 
            db.session.commit() 
        res = requests.post(url, json=data, timeout=2000)
        if archivo:
            remove(str(os.path.join(uploads_dir, secure_filename(archivo.filename))))
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        
        return render_template("send.html", message="Enviado con exito", numeros=numeros, iconos=iconos, paisuser=paisuser)
    if request.method == 'GET':
       
        return render_template("send.html", numeros=numeros, iconos=iconos, paisuser=paisuser)

@app.route("/asignar", methods=["GET", "POST"])
@login_required
def asignar():
    if request.method == 'GET':
        if current_user.is_admin():
            usuarios = Usuario.query.all()
            lineas = Linea.query.all()
            asignaciones = Asignacion.query.all()
            lista = []
            for usuario in usuarios:
                asiglista = []
                asiglista.append(usuario.username)
                user = f'{usuario.name}: {usuario.username}'
                asiglista.append(user)
                for linea in lineas:
                    apen = False
                    for asig in asignaciones:
                        if asig.user_id == usuario.id and asig.linea_id == linea.id:
                            asiglista.append(["2705", linea.id])
                            apen = True
                    if not(apen):
                            asiglista.append(["274C", linea.id])
                lista.append(asiglista)
            return render_template("asignaciones.html", usuarios=usuarios, lineas=lineas, asignaciones=lista)
        else:
            return redirect(url_for('send'))

    if request.method == 'POST':
        usuario = request.form.get("username")
        linea_id = request.form.get("linea")
        elemento = request.form.get("element")
        user = Usuario.query.filter_by(username=usuario).first()
        linea = Linea.query.filter_by(id=linea_id).first()
        if user and linea:
            if str(elemento) == "2705":
                asignacion = Asignacion.query.filter_by(user_id=user.id).filter_by(linea_id=linea.id).first()
                print(asignacion)
                db.session.delete(asignacion)
                db.session.commit()

            elif str(elemento) == "274C":
                nueva = Asignacion(user_id=user.id, linea_id=linea.id)
                db.session.add(nueva)   
                db.session.commit()
        return redirect(url_for('asignar'))



@app.route("/linea", methods=["GET", "POST"])
@login_required
def linea():
    if current_user.is_admin():
        lineas = Linea.query.all()
        if request.method == 'GET':
            return render_template("linea.html", lineas=lineas)

        if request.method == 'POST':
                # Get form information.
            form = int(request.form.get("formhidden"))
            if form == 1:
                name = request.form.get("name")
                apiurl = request.form.get("apiurl")
                token = request.form.get("token")
                nueva = Linea(name=name, api_url=apiurl, token=token)
                db.session.add(nueva)   
                db.session.commit()
            if form == 2:
                linea = request.form.get("linea")
                mylinea = Linea.query.filter_by(name=linea).first()
                asignaciones = Asignacion.query.filter_by(linea_id=mylinea.id).all()
                for asig in asignaciones:
                    db.session.delete(asig)
                db.session.delete(mylinea)
                db.session.commit()
            if form == 3:
                oldline = request.form.get("oldline")
                name = request.form.get("name")
                apiurl = request.form.get("apiurl")
                token = request.form.get("token")
                mylinea = Linea.query.filter_by(name=oldline).first()
                mylinea.name = name
                mylinea.api_url = apiurl
                mylinea.token = token
                db.session.commit()
            return redirect(url_for('linea'))
    else:
        return redirect(url_for('send'))

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.is_admin():
        usuarios = Usuario.query.all()
        
        if request.method == 'GET':
            # f = open('mensaje.txt')
            # mensajeoculto = f.read()
            # f.close()
            return render_template("admin.html", usuarios=usuarios)
        
        if request.method == 'POST':
            form = int(request.form.get("formhidden"))
            if form == 1:
                name = request.form.get("name")
                username = request.form.get("username")
                psw = request.form.get("password")
                empresa = request.form.get("empresa")
                pais = str(request.form.get("selectorflags"))

                # Make sure the user exists.
                user = Usuario.query.filter_by(username=username).first()
                if user:
                    return render_template("error.html", message="Username already exists")
                
                nuevo = Usuario(name=name.capitalize(), username=username, empresa=empresa, pais=pais)
                nuevo.password_hash = generate_password_hash(psw)
                nuevo.admin = False
                db.session.add(nuevo)   
                db.session.commit()
            if form == 2:
                olduser = request.form.get("olduser")
                name = request.form.get("name")
                username = request.form.get("username")
                psw = request.form.get("password")
                empresa = request.form.get("empresa")
                pais = str(request.form.get("selectorflags"))
                myuser = Usuario.query.filter_by(username=olduser).first()
                myuser.username = username
                myuser.name = name
                myuser.empresa = empresa
                myuser.pais = pais
                if psw:
                    myuser.password_hash = generate_password_hash(psw)
                db.session.commit()
            if form == 3:
                user = request.form.get("username")
                myuser = Usuario.query.filter_by(username=user).first()
                asignaciones = Asignacion.query.filter_by(user_id=myuser.id).all()
                for asig in asignaciones:
                    db.session.delete(asig)
                db.session.delete(myuser)
                db.session.commit()
            if form == 4:
                msjoculto = request.form.get("mensaje")
                f = open("mensaje.txt", "w")
                f.write(msjoculto)
                f.close()
            if form == 5:
                user = request.form.get("username")
                myuser = Usuario.query.filter_by(username=user).first()
                myuser.mensajeoculto = not(myuser.mensajeoculto)
                db.session.commit()
            return redirect(url_for('admin'))
    else:
        return redirect(url_for('send'))

@app.route("/envios/<int:user_id>")
@login_required
def envios(user_id):
    if current_user.is_admin():
        myuser = Usuario.query.get(user_id)
        if myuser is None:
            return render_template("error.html", message="No user.")
        enviados = Enviado.query.filter_by(user=myuser.username).all()
        cantidad = len(enviados)
        return render_template("enviados.html", enviados=enviados, usuario=myuser, cantidad=cantidad)

@app.route("/lineas/<int:user_id>", methods=["GET", "POST"])
@login_required
def lineas(user_id):
    if current_user.is_admin():
        if request.method == 'GET':
            myuser = Usuario.query.get(user_id)
            if myuser is None:
                return render_template("error.html", message="No user.")
            asignaciones = Asignacion.query.filter_by(user_id=myuser.id).all()
            lineas = []
            for asig in asignaciones:
                agreg = Linea.query.get(asig.linea_id)
                lineas.append(agreg)
            return render_template("lineasuser.html", lineas=lineas, usuario=myuser)
        if request.method == 'POST':
            user = int(request.form.get("user"))
            linea = int(request.form.get("linea"))
            asignacion = Asignacion.query.filter_by(user_id=user).filter_by(linea_id=linea).first()
            db.session.delete(asignacion)
            db.session.commit()
            return redirect(url_for('lineas', user_id=user_id))

