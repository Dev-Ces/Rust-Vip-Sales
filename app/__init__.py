import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Import routes after app creation to avoid circular imports
    with app.app_context():
        try:
            from .routes import main
            app.register_blueprint(main)
            db.create_all()
        except Exception as e:
            print(f"Error importing routes: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    return app 