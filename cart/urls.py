# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *


urlpatterns = patterns('cart.views',
    (r'^$', 'index'),
    (r'^checkout/$', 'checkout'),
    (r'^delivery/$', 'delivery'),
    (r'^payment/$', 'payment'),
    (r'^payment/([\w_\-]+)/$', 'payment'),
    (r'^complete/([\w_\-]+)/$', 'complete'),

    (r'^add/$', 'add', {}, 'cart_add'),
    (r'^clear/$', 'clear', {}, 'cart_clear'),
    (r'^update/$', 'update', {}, 'cart_update'),
    
)
