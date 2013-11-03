# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *


urlpatterns = patterns('shop.views',
    
    (r'^$', 'index'),
    (r'^([\w\-_]+)/$', 'index'),
    (r'^([\w\-_]+)/([\w\-_]+)/$', 'product'),

)

