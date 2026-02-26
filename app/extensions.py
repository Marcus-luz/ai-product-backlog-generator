from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager # Importa LoginManager
from flask_jwt_extended import JWTManager # Importa JWTManager
from flask_migrate import Migrate # Importa Migrate

db = SQLAlchemy()
login_manager = LoginManager() # Instancia o LoginManager
jwt = JWTManager() # Instancia o JWTManager
migrate = Migrate() # Instancia o Migrate