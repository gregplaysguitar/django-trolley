# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^admin/', include(admin.site.urls)),

    url(r'^cart/', include('cart.urls')),
    url(r'^', include('shop.urls')),

)
