# -*- coding: utf-8 -*-

try:
    from django.conf.urls import *
except ImportError:
    from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^admin/', include(admin.site.urls)),

    url(r'^cart/', include('cart.urls')),
    url(r'^payment/', include('payment.urls')),
    url(r'^', include('shop.urls')),

)
