from flask import Flask
from config import config
from extensions import db, migrate
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from blueprints.tickets import tickets_bp
    from blueprints.analytics import analytics_bp

    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    @app.route('/')
    def index():
        return "AI Ticketing System Backend API"

    return app

app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    app.run()
