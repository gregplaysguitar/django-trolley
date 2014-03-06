import functools
import importlib

from django.utils.importlib import import_module

from cart import get_helper_module, settings


def get_option(name, default=None, *args, **kwargs):
    helper_module = get_helper_module()
    if helper_module and hasattr(helper_module, name):
        return getattr(helper_module, name)(*args, **kwargs)
    else:
        if isinstance(default, str):
            bits = default.split('.')
            mod = import_module('.'.join(bits[:-1]))
            return getattr(mod, bits[-1])
        else:
            return default

get_cart = functools.partial(get_option, 'get_cart', 'cart.api.Cart')
get_order_detail = functools.partial(get_option, 'get_order_detail')
get_add_form = functools.partial(get_option, 'get_add_form', 'cart.forms.AddToCartForm')
get_order_form = functools.partial(get_option, 'get_order_form', 'cart.forms.OrderForm')
get_order_detail_form = functools.partial(get_option, 'get_order_detail_form')


def get_render_function():
    '''Gets function used to render templates - by default, 
       django.shortcuts.render_to_response, but could be coffins version, or
       custom.'''
    
    bits = settings.TEMPLATE_RENDERER.split('.')
    renderer_module = importlib.import_module('.'.join(bits[:-1]))
    return getattr(renderer_module, bits[-1])