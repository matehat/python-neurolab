import os, sys
from os.path import split, abspath, join

# Probing setup

_web = split(abspath(__file__))[0]

if 'NEUROPY_PATH' in os.environ:
    basedir = os.environ['NEUROPY_PATH']
else:
    basedir = split(_web)[0]

if basedir not in sys.path:
    sys.path.append(basedir)
    
import config

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Mathieu Blais-D\'Amours', 'mathieu.blais-damours.1@ulaval.ca'),
)
AUTHENTICATION_BACKENDS = (
    'neurolab.db.auth.Backend',
)
SESSION_ENGINE = 'mongoengine.django.sessions'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
LOGIN_URL = '/login/'

STATIC_URL = config.MEDIA_URL
STATICFILES_DIRS = (config.MEDIA,)

MANAGERS = ADMINS

DATABASES = { # Leave all that blank, we're not using a django database driver natively
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

TIME_ZONE = 'America/Montreal'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False
USE_L10N = False

SECRET_KEY = config.SECRET_KEY

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'web.urls'

TEMPLATE_DIRS = (config.TEMPLATES['DJANGO'],)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.csrf',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'web',
    'gunicorn',
)

import matplotlib
matplotlib.use('Agg')
