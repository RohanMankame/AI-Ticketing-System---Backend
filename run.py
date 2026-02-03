import os
from dotenv import load_dotenv
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

load_dotenv()

from flask import Flask
from config import config
from extensions import db, migrate

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    CORS(app)
    

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Models
    from models import Ticket, KnowledgeArticle

    # Register Blueprints
    from blueprints.tickets import tickets_bp
    from blueprints.analytics import analytics_bp
    from blueprints.knowledge import knowledge_bp

    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge')

    # Swagger UI (loads static/openapi.json)
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/openapi.json'  # ensure openapi.json is placed at project_root/static/openapi.json

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "AI Ticketing System API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/')
    def index():
        return "AI Ticketing System Backend API"

    return app

app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    app.run()