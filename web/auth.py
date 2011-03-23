from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login as _login, logout as _logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf.urls.defaults import *

def secured_url(*args):
    args = list(args)
    if callable(args[1]):
        args[1] = login_required(args[1])
    return url(*args)


def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')
    
    if 'username' in request.POST:
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                _login(request, user)
                return HttpResponseRedirect('/')
            else:
                print "Deactivated"
                messages.error(request, "The user specified has been deactivated")
        else:
            print "No match"
            messages.error(request, "The information you entered do not match any known user.")
    
    return render_to_response('login.html', context_instance=RequestContext(request))

def logout(request):
    _logout(request)
    return HttpResponseRedirect('/login/')

urlpatterns = patterns('',
    url(r'^login/$', login),
    url(r'^logout/$', logout),
)