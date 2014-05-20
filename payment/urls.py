try:
    from django.conf.urls import *
except ImportError:
    from django.conf.urls.defaults import *

urlpatterns = patterns('payment.views',
    (r'^$', 'index'),
        
)
