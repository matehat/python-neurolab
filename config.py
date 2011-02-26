# Django settings for app project.

import os, sys
import mongoengine
from os.path import split, abspath, join

# Probing setup

if 'NEUROLAB_PATH' in os.environ:
    BASE = os.environ['NEUROLAB_PATH']
else:
    BASE = split(abspath(__file__))[0]

if BASE not in sys.path:
    sys.path.append(BASE)
    
DEBUG = True

ASSETS = join(BASE, 'assets')
MEDIA = join(ASSETS, 'media/')
TEMPLATES = {
    'DJANGO': join(ASSETS, 'django'),
    'MUSTACHE': join(ASSETS, 'mustache'),
}

MONGO_PORT = 8001
MONGO_DB = 'neurolab'

QUEUES = {
    'graphics': {
        'workers': 1,
        'time': 1.0
    },
    'data': {
        'workers': 2,
        'time': 0.5,
    },
    'files': {
        'workers': 1,
        'time': 1.0,
    }
}

HTTP_WORKERS = 1
HTTP_ADDRESS = '127.0.0.1:4000'

MEDIA_URL = '/media/'
SUPPORTED_FORMATS = ('tuckerdavis', 'matlab', 'hierarchicaldata')

SECRET_KEY = 's6@q_@#++)ubmx04x+rs_j^f4ywnz1c0-)1r&a97v))l1n14tg'