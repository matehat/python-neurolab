from mongoengine import *
from node import settings
import mongoengine

connect(
    getattr(settings, 'MONGO_DATABASE', 'neurolab'),
    host=getattr(settings, 'MONGO_HOST', '127.0.0.1'),
    port=getattr(settings, 'MONGO_PORT', 27017),
    username=getattr(settings, 'MONGO_USERNAME', None),
    password=getattr(settings, 'MONGO_PASSWORD', None)
)

__all__ = list(mongoengine.__all__) + []
