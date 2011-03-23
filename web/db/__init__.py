from django.conf.urls.defaults import *

import datasources, db

urlpatterns = patterns('',
    url(r'^datasources/',   include(datasources.urlpatterns)),
    url(r'^db/',            include(db.urlpatterns)),
)