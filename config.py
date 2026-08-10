import os
import datetime
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-carebridge-key'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/carebridge'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-super-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=7)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CLOUDFLARE_API_KEY = os.environ.get('CLOUDFLARE_API_KEY')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    CLOUDFLARE_ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    CLOUDFLARE_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
