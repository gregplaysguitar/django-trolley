from django.conf import settings
import os

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


