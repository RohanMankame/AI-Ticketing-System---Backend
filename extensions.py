import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db_url = os.environ.get('DATABASE_URL_Prod')
print(f"DEBUG: DATABASE_URL_Prod")

if not db_url:
    raise ValueError("DATABASE_URL_Prod environment variable is not set!")

class Config:
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()
migrate = Migrate()