from django.conf import settings
import os

PRODUCT_TYPES = getattr(
    settings,
    'CART_PRODUCT_TYPES',
    (('shop', 'product'),)
)
ALLOW_ADD_EXISTING = True

ORDER_DETAIL_MODEL = getattr(
    settings,
    'CART_ORDER_DETAIL_MODEL',
    None
)


# list of fields to show in the checkout form, eg discount code - 
# must correpond to fields in the ORDER_DETAIL_MODEL class
CHECKOUT_FORM_FIELDS = getattr(
    settings,
    'CART_CHECKOUT_FORM_FIELDS',
    None
) 

SKIP_CHECKOUT = getattr(settings, 'CART_SKIP_CHECKOUT', False)

ORDER_STATUSES = getattr(
    settings,
    'CART_ORDER_STATUSES',
    [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
    ]
)


MANAGERS = getattr(
    settings,
    'CART_MANAGERS',
    settings.MANAGERS
)

ALLOWED_CARD_TYPES = ('Visa', 'MasterCard') # from ('Visa', 'MasterCard', 'American Express', 'Discover')


PAYMENT_BACKEND = getattr(
    settings,
    'CART_PAYMENT_BACKEND',
    None
)
PAYMENT_DEBUG = getattr(
    settings,
    'CART_PAYMENT_DEBUG',
    settings.DEBUG
)
LOG_DIR = getattr(
    settings,
    'CART_LOG_DIR',
    os.path.join(settings.PROJECT_ROOT, 'log')
)


WEBPAY_CLIENT_ID = getattr(
    settings,
    'CART_WEBPAY_CLIENT_ID',
    None
)
WEBPAY_CERTIFICATE_PATH = getattr(
    settings,
    'CART_WEBPAY_CERTIFICATE_PATH',
    None
)
WEBPAY_CERTIFICATE_PASSWORD = getattr(
    settings,
    'CART_WEBPAY_CERTIFICATE_PASSWORD',
    None
)
WEBPAY_PORT = getattr(
    settings,
    'CART_WEBPAY_PORT',
    None
)


