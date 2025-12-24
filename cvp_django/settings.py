import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
env_path = BASE_DIR / '.env'
if env_path.exists():
    try:
        with env_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and (key not in os.environ or os.environ.get(key) == ''):
                        os.environ[key] = val
    except Exception:
        pass

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*']



# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'api.apps.ApiConfig',
    'admin_auth.apps.AdminAuthConfig',
    'web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Session Settings
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Reset session timer on every request

ROOT_URLCONF = 'cvp_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'frontend'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cvp_django.wsgi.application'
ASGI_APPLICATION = 'cvp_django.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}

FASTAPI_BASE_URL = os.environ.get('FASTAPI_BASE_URL', 'http://localhost:8000')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
PAYSTACK_BASE_URL = os.environ.get('PAYSTACK_BASE_URL', 'https://api.paystack.co')

BLOCKCHAIN_NETWORKS = {
    'BITCOIN': {
        'type': 'blockcypher',
        'base_url': os.environ.get('BITCOIN_API_BASE', 'https://api.blockcypher.com/v1/btc/main'),
        'token': os.environ.get('BLOCKCYPHER_TOKEN', ''),
        'min_confirmations': int(os.environ.get('BTC_MIN_CONFIRMATIONS', '1')),
    },
    'ERC20': {
        'type': 'evm',
        'rpc_url': os.environ.get('ETHEREUM_RPC_URL', ''),
        'min_confirmations': int(os.environ.get('ETH_MIN_CONFIRMATIONS', '3')),
    },
    'BEP20': {
        'type': 'evm',
        'rpc_url': os.environ.get('BSC_RPC_URL', ''),
        'min_confirmations': int(os.environ.get('BSC_MIN_CONFIRMATIONS', '5')),
    },
    'POLYGON': {
        'type': 'evm',
        'rpc_url': os.environ.get('POLYGON_RPC_URL', ''),
        'min_confirmations': int(os.environ.get('POLYGON_MIN_CONFIRMATIONS', '10')),
    },
    'ARBITRUM': {
        'type': 'evm',
        'rpc_url': os.environ.get('ARBITRUM_RPC_URL', ''),
        'min_confirmations': int(os.environ.get('ARBITRUM_MIN_CONFIRMATIONS', '6')),
    },
    'AVALANCHE': {
        'type': 'evm',
        'rpc_url': os.environ.get('AVALANCHE_RPC_URL', ''),
        'min_confirmations': int(os.environ.get('AVALANCHE_MIN_CONFIRMATIONS', '6')),
    },
    'TRC20': {
        'type': 'tron',
        'base_url': os.environ.get('TRON_API_BASE', 'https://api.trongrid.io'),
        'api_key': os.environ.get('TRON_API_KEY', ''),
    },
}