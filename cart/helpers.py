import functools

from django.utils.importlib import import_module

from cart import get_helper_module


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




"""

def get_cart():
    helper_module = get_helper_module()
    if helper_module and hasattr(helper_module, 'get_cart'):
        helper_module.get_cart()
    else:
        from api import Cart
        return Cart

def get_order_detail():
    helper_module = get_helper_module()
    if helper_module and hasattr(helper_module, 'get_order_detail'):
        helper_module.get_order_detail()
    else:
        return None

def (product):
    helper_module = get_helper_module()
    if helper_module and hasattr(helper_module, 'get_add_form'):
        return helper_module.get_add_form(product)
    else:
        from forms import AddToCartForm
        return AddToCartForm

def get_order_form():
"""
