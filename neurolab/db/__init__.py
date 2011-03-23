from mongoengine import *

from config import MONGO_DB, MONGO_PORT

def dereference(dbref):
    from mongoengine.base import get_document
    doc = mongodb().dereference(dbref)
    return get_document(doc['_cls'].split('.')[-1])._from_son(doc)

def mongodb(collection=None):
    from mongoengine.connection import _get_db
    db = _get_db()
    if collection is not None:
        return getattr(db, collection)
    else:
        return db


connect(MONGO_DB, port=MONGO_PORT)
from neurolab.db.auth import SafeDocument
from neurolab.db.models import *