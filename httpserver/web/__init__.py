from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf.urls.defaults import *

import auth
import config

def media_url(request): # Context Processor to inject media URL in templates
    return {'MEDIA_URL': config.MEDIA_URL}


@auth.secure
def db(request):
    return render_to_response('interfaces/db.html', context_instance=RequestContext(request))


urlpatterns = patterns('',
    url(r'^login/$', auth.login),
    url(r'^logout/$', auth.logout),
    
    url(r'^$', db),
    
    url(r'^media/(?P<path>.*)$', 'django.contrib.staticfiles.views.serve', {'document_root': config.MEDIA}),
    url(r'^t/(?P<path>.*)$', 'django.contrib.staticfiles.views.serve', 
        {'document_root': "%s/" % config.TEMPLATES['MUSTACHE']}),
)