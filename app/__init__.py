from flask import Flask
from flask_cors import CORS
import logging

from app.config import Config
from app.extensions import init_extensions

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='../static', static_url_path='/static')
    app.config.from_object(config_class)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    init_extensions(app)
    
    # Temporarily importing register_blueprints
    from app.api import register_blueprints
    register_blueprints(app)
    
    return app
