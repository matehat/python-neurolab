import datetime
from django.utils.hashcompat import md5_constructor, sha_constructor
from django.utils.encoding import smart_str
from django.contrib.auth.models import AnonymousUser

from neurolab.db import *

REDIRECT_FIELD_NAME = 'next'

def get_hexdigest(algorithm, salt, raw_password):
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'md5':
        return md5_constructor(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return sha_constructor(salt + raw_password).hexdigest()
    raise ValueError('Got unknown password algorithm type in password')


class Permission(Document):
    codes = {
        'read': 1,
        'write': 2,
        'admin': 4,
    }
    user = ReferenceField('User')
    permission_code = IntField(choices=codes.values())

class SafeDocument(Document):
    permissions = ListField(ReferenceField(Permission))
    
    @classmethod
    def readable_by(cls, user):
        return cls.objects(**user.Q('read'))
    
    @classmethod
    def writable_by(cls, user):
        return cls.objects(**user.Q('write'))
    
    @classmethod
    def administrable_by(cls, user):
        return cls.objects(**user.Q('admin'))
    
    
    def permit_user(self, user, perm):
        perm, created = Permission.objects.get_or_create(user=user, permission_code=Permission.codes[perm])
        self.permissions.append(perm)
    
    def disallow_user(self, user, perm):
        perm, created = Permission.objects.get_or_create(user=user, permission_code=Permission.codes[perm])
        if perm in self.permissions:
            self.permissions.remove(perm)
    
    
    meta = {'abstract': True}


class User(Document):
    """
    A User document that aims to mirror most of the API specified by Django
    at http://docs.djangoproject.com/en/dev/topics/auth/#users
    """
    username = StringField(max_length=30, required=True)
    first_name = StringField(max_length=30)
    last_name = StringField(max_length=30)
    email = StringField()
    password = StringField(max_length=128)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(default=datetime.datetime.now)
    date_joined = DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.username
    
    def get_full_name(self):
        """
        Returns the users first and last names, separated by a space.
        """
        full_name = u'%s %s' % (self.first_name or '', self.last_name or '')
        return full_name.strip()
    
    def is_anonymous(self):
        return False
    
    def is_authenticated(self):
        return True
    
    def set_password(self, raw_password):
        """
        Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.
        """
        from random import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random()), str(random()))[:5]
        hash = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hash)
        self.save()
        return self
    
    def check_password(self, raw_password):
        """
        Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """
        algo, salt, hash = self.password.split('$')
        return hash == get_hexdigest(algo, salt, raw_password)
    
    @classmethod
    def create_user(cls, username, password, email=None):
        """
        Create (and save) a new user with the given username, password and
        email address.
        """
        now = datetime.datetime.now()
        
        # Normalize the address by lowercasing the domain part of the email
        # address.
        if email is not None:
            try:
                email_name, domain_part = email.strip().split('@', 1)
            except ValueError:
                pass
            else:
                email = '@'.join([email_name, domain_part.lower()])
                
        user = cls(username=username, email=email, date_joined=now)
        user.set_password(password)
        user.save()
        return user
    
    def get_and_delete_messages(self):
        return []
    
    
    def permission(self, perm):
        if not hasattr(self, '_permissions'):
            self._permissions = {}
        if perm not in self._permissions:
            self._permissions[perm] = Permission.objects(
                user=self, permission_code__mod=(Permission.codes[perm],0)
            )
        return self._permissions[perm]
    
    def permit_for(self, object, perm):
        if isinstance(obj, SafeDocument):
            obj.permit_user(self, perm)
    
    def Q(self, permission):
        return {'permissions__in': self.permission(permission)}
    

class Backend(object):
    """
    Authenticate using MongoEngine and neurolab.core.auth.User.
    """
    
    def authenticate(self, username=None, password=None):
        user = User.objects(username=username).first()
        if user:
            if password and user.check_password(password):
                return user
        return None
    
    def get_user(self, user_id):
        return User.objects.with_id(user_id)
    

