from cart import get_helper_module



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

def get_add_form(product):
    helper_module = get_helper_module()
    if helper_module and hasattr(helper_module, 'get_add_form'):
        return helper_module.get_add_form(product)
    else:
        from forms import AddToCartForm
        return AddToCartForm
