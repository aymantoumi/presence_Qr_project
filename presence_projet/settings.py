import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Changez ceci en production !
SECRET_KEY = 'django-insecure-@votre-cle-secrete-ici'

DEBUG = True

ALLOWED_HOSTS = []

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    
    # Nos applications
    'comptes.apps.ComptesConfig',
    'presence.apps.PresenceConfig',
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

ROOT_URLCONF = 'presence_projet.urls'

# Configuration des Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Pointeur vers le dossier global
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

WSGI_APPLICATION = 'presence_projet.wsgi.application'

# Configuration de la base de données PostgreSQL
# Assurez-vous d'avoir créé cette base de données et cet utilisateur dans PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'presence_db',      # Nom de votre DB
        'USER': 'postgres', # Votre utilisateur DB
        'PASSWORD': '1234',
        'HOST': 'localhost',             
        'PORT': '5432',                  
    }
}

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Fichiers statiques (CSS, JS, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'comptes.Utilisateur'

# URL de redirection après connexion/déconnexion
LOGIN_REDIRECT_URL = 'dashboard_redirect' # Vue de redirection
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'