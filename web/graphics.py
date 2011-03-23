from django.http import HttpResponse
from django.conf.urls.defaults import *

from web.auth import secured_url as secured

def component_graphic(request, component_id, width, height, format):
    from neurolab.db.models import *
    
    width, height = int(width), int(height)
    try:
        component = Component.objects.with_id(component_id)
    except Component.DoesNotExist:
        raise Http404
    
    image, mimetype = component.grapher(request.GET).get_image(width, height, format)
    image.seek(0)
    return HttpResponse(image.read(), mimetype=mimetype)

urlpatterns = patterns('',
    secured(r'^g/(?P<component_id>[0-9a-f]+)/(?P<width>\d+)x(?P<height>\d+)\.(?P<format>[a-z]+)$', component_graphic),
)