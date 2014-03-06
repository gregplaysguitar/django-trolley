# -*- coding: utf-8 -*-

try:
    from django.conf.urls import *
except ImportError:
    from django.conf.urls.defaults import *


urlpatterns = patterns('shop.views',
    
    (r'^$', 'index'),
    (r'^([\w\-_]+)/$', 'index'),
    (r'^([\w\-_]+)/([\w\-_]+)/$', 'product'),

)

