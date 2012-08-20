from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

import settings as cart_settings


__version__ = '1.1'
VERSION = tuple(map(int, __version__.split('.'))) + ('dev',)


#import_module('cart_helpers')

def get_helper_module():
    '''Get the helper module as defined in the settings.'''
    
    if cart_settings.HELPER_MODULE:
        try:
            package = import_module(cart_settings.HELPER_MODULE)
        except ImportError, e:
            raise ImproperlyConfigured(u'The CART_HELPER_MODULE setting refers to a ' \
                                        'non-existent package, or the import failed ' \
                                        'due to an error. Error details: %s' % e)
        return package
    else:
        return None

