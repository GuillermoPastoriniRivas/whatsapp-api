from decouple import config

class Config:
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://qmckbpetcbyeum:f0a97818832c585e960e0c3a7a85e10894d1c3d428687d08e4e1e7bdc02a9d3c@ec2-3-211-48-92.compute-1.amazonaws.com:5432/d45jrau572mh69'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='localhost')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}