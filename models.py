import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):

    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    empresa = db.Column(db.String(200), nullable=True)
    admin = db.Column(db.Boolean, default=False)

    def is_admin(self):
        return self.admin


class Linea(db.Model):

    __tablename__ = 'linea'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    api_url = db.Column(db.String(200),  nullable=False)
    token = db.Column(db.String(16), nullable=False)

class Asignacion(db.Model):

    __tablename__ = 'asignacion'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    linea_id = db.Column(db.Integer, db.ForeignKey("linea.id"), nullable=False)

class Enviado(db.Model):

    __tablename__ = 'enviado'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    linea = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.BigInteger, nullable=False)
    prefijo = db.Column(db.Integer, nullable=False)
    mensaje = db.Column(db.String(200), nullable=True)
    archivo = db.Column(db.String(200),  nullable=True)
