import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
SECRET_KEY = os.getenv('SECRET_KEY', 'unsafe-development-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [
    'airesilientcodingassessmentportal.vercel.app',
]
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'assessments']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'portal.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'portal.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = 'en-us', 'Asia/Kolkata', True, True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
JUDGE0_URL = os.getenv('JUDGE0_URL', 'https://ce.judge0.com').rstrip('/')
JUDGE0_API_KEY = os.getenv('JUDGE0_API_KEY', '')
AI_REVIEW_API_URL = os.getenv('AI_REVIEW_API_URL', 'https://api.openai.com/v1/chat/completions').rstrip('/')
AI_REVIEW_API_KEY = os.getenv('AI_REVIEW_API_KEY', '')
AI_REVIEW_MODEL = os.getenv('AI_REVIEW_MODEL', 'gpt-4o-mini')
AI_REVIEW_PROVIDER = os.getenv('AI_REVIEW_PROVIDER', 'ollama').lower()
AI_REVIEW_OLLAMA_URL = os.getenv('AI_REVIEW_OLLAMA_URL', 'http://127.0.0.1:11434/api/chat').rstrip('/')
CODE_LOG_INTERVAL_SECONDS = int(os.getenv('CODE_LOG_INTERVAL_SECONDS', '30'))
