# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.views.generic.base import RedirectView
from django.utils.functional import lazy
from django.core.urlresolvers import reverse

reverse_lazy = lazy(reverse, str)


urlpatterns = patterns('cart.views',
    (r'^$', 'checkout'),
    
    # dummy url for backwards-compatibility - allows reversing of cart.views.index
    (r'^$', 'index'), 
    
    # catch old static links to checkout/
    (r'^checkout/$', RedirectView.as_view(url=reverse_lazy('cart.views.checkout'))),
    
    (r'^delivery/$', 'delivery'),
    (r'^payment/$', 'payment'),
    (r'^payment/([\w_\-]+)/$', 'payment'),
    (r'^payment/([\w_\-]+)/([\w_\-]+)/$', 'payment'),
    (r'^complete/([\w_\-]+)/$', 'complete'),

    (r'^add/$', 'add', {}, 'cart_add'),
    (r'^clear/$', 'clear', {}, 'cart_clear'),
    (r'^update/$', 'update', {}, 'cart_update'),
    
)
