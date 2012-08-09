from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

import settings as cart_settings
import helpers


__version__ = '1.1'
VERSION = tuple(map(int, __version__.split('.'))) + ('dev',)


def get_helper_module():
    '''Get the helper module as defined in the settings.'''
    
    if cart_settings.HELPER_MODULE:
        try:
            package = import_module(cart_settings.HELPER_MODULE)
        except ImportError:
            raise ImproperlyConfigured(u'The CART_HELPER_MODULE setting refers to a ' \
                                        'non-existent package.')
        return package
    else:
        return helpers



