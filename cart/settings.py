from django.conf import settings

PRODUCT_TYPES = getattr(
    settings,
    'CART_PRODUCT_TYPES',
    (('shop', 'product'),)
)


ALLOW_ADD_EXISTING = True