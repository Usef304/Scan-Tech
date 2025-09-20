from flask import Flask
from flask_caching import Cache
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize extensions
cache = Cache()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    
    # Cache configuration
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
    
    # Initialize extensions with app
    cache.init_app(app)
    csrf.init_app(app)
    
    # Enable HTTPS enforcement in production
    if os.environ.get('FLASK_ENV') == 'production':
        Talisman(app, content_security_policy=None)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app