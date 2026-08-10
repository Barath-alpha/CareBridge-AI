import ssl
from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import Config

bcrypt = Bcrypt()
jwt = JWTManager()

# Global database handle (pymongo or local fallback)
mongo_client = None
db = None


def _try_mongo(uri: str):
    """Attempt to connect to MongoDB Atlas. Returns (client, db) or (None, None)."""
    try:
        import certifi
        client = MongoClient(
            uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )
        client.admin.command('ping')
        return client, client.get_database()
    except Exception as e:
        print(f"[WARNING] MongoDB Atlas unreachable: {e.__class__.__name__}: {str(e)[:120]}")
        return None, None


def create_app(config_class=Config):
    global mongo_client, db

    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # ── Try MongoDB Atlas first ──────────────────────────────
    mongo_client, db = _try_mongo(app.config['MONGO_URI'])

    if db is not None:
        print("[OK] Connected to MongoDB Atlas successfully.")
    else:
        # ── Fallback: local JSON-based database ──────────────
        from app.local_db import local_db
        db = local_db
        print("[INFO] Using local JSON database (carebridge_local.json).")
        print("       -> To use MongoDB Atlas, reset the password in Atlas dashboard.")

    # ── Register Blueprints ──────────────────────────────────
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.recovery_routes import recovery_bp
    from app.routes.escalation_routes import escalation_bp
    from app.routes.caregiver_routes import caregiver_bp
    from app.routes.clinician_routes import clinician_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.document_routes import document_bp
    from app.routes.journal_routes import journal_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(recovery_bp)
    app.register_blueprint(escalation_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(clinician_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(journal_bp)

    return app
