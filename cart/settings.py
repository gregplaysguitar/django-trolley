from django.conf import settings

PRODUCT_TYPES = getattr(
    settings,
    'CART_PRODUCT_TYPES',
    (('shop', 'product'),)
)


ALLOW_ADD_EXISTING = True



PAYMENT_BACKEND = getattr(
    settings,
    'CART_PAYMENT_BACKEND',
    None
)