from decouple import config

class Config:
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://rbjfjrgvcyzhim:8508dc79c4f26ab684ce7ebfd840b4d1a37eef670036f007c7b47ee069c7bee5@ec2-52-207-93-32.compute-1.amazonaws.com:5432/dr7e28ncjras2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='localhost')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}