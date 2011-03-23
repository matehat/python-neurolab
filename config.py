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

ASSETS = join(BASE, 'web/assets')
MEDIA = join(ASSETS, 'media/')
TEMPLATES = {
    'DJANGO': join(ASSETS, 'templates'),
}

MONGO_PORT = 8001
MONGO_DB = 'neurolab'

QUEUES = {
    'output': {
        'workers': 1,
        'time': 1.0
    },
    'processing': {
        'workers': 2,
        'time': 0.5,
    },
    'files': {
        'workers': 1,
        'time': 1.0,
    }
}

HTTP_WORKERS = 2
HTTP_ADDRESS = '127.0.0.1:4000'

MEDIA_URL = '/media/'

CHUNKSIZES = {
    'read': 20*(2**20),
    'fft': 2**14
}
FILEFORMATS = ('tuckerdavis', 'axon')
EXTENSIONS = (
    'basis.waves', 'basis.fft', 'basis.scalogram',
    'project.chronic',
)

SECRET_KEY = 's6@q_@#++)ubmx04x+rs_j^f4ywnz1c0-)1r&a97v))l1n14tg'