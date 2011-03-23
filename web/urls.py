from django.conf.urls.defaults import *
from web import db, auth, graphics
import config

def media_url(request): # Context Processor to inject media URL in templates
    return {'MEDIA_URL': config.MEDIA_URL}

urlpatterns = patterns('',
    url(r'^$',  'django.views.generic.simple.redirect_to', {'url': '/db/'}),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': config.MEDIA}),
) 

urlpatterns += (
    auth.urlpatterns + 
    db.urlpatterns +
    graphics.urlpatterns
)