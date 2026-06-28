import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # =========================
    # SECURITY KEY
    # =========================
    # IMPORTANT: Change this in production
    SECRET_KEY = os.environ.get("SECRET_KEY", "ChameleonNexusSecretKey")

    # =========================
    # DATABASE CONFIG - SUPABASE
    # =========================
    # Supabase URL and Keys (loaded from .env)
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    # =========================
    # CLOUDINARY CONFIG
    # =========================
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

    # =========================
    # UPLOAD CONFIG
    # =========================
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # =========================
    # DEBUG SETTINGS
    # =========================
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    
    # =========================
    # SQLALCHEMY (Legacy - Kept for compatibility, but not used)
    # =========================
    # Note: SQLAlchemy is replaced by Supabase Client
    # These are kept for reference but not used in new version
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # In production, ensure SECRET_KEY is set in environment
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production environment")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration dictionary for different environments
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get("FLASK_ENV", "development")
    return config.get(env, DevelopmentConfig)