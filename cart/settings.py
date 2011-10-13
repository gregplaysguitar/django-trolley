import os

from django.conf import settings


"""A list of (app, model) tuples specifying what can go in the cart."""
PRODUCT_TYPES = getattr(
    settings,
    'CART_PRODUCT_TYPES',
    (('shop', 'product'),)
)


"""A custom model which works in the same way as django's AUTH_PROFILE_MODULE
   to add custom data to an order. Use it for adding data which is custom to 
   your project, such as a separate delivery address."""
ORDER_DETAIL_MODEL = getattr(
    settings,
    'CART_ORDER_DETAIL_MODEL',
    None
)


"""List of fields to show in the checkout form, eg discount code - 
   must correpond to fields in the ORDER_DETAIL_MODEL class. Fields
   in the ORDER_DETAIL_MODEL but not listed here will show on the 
   delivery details page."""
CHECKOUT_FORM_FIELDS = getattr(
    settings,
    'CART_CHECKOUT_FORM_FIELDS',
    []
) 


"""Set to true if you want to go straight from adding a product to the cart
   to the delivery details form.""" 
SKIP_CHECKOUT = getattr(settings, 'CART_SKIP_CHECKOUT', False)


"""Define custom order statuses here - must include the keys 'confirmed' and
   'shipped', although the long name can be anything you want."""
ORDER_STATUSES = getattr(
    settings,
    'CART_ORDER_STATUSES',
    [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
    ]
)


"""A list of (email, name) tuples who should receive order notifications."""
MANAGERS = getattr(
    settings,
    'CART_MANAGERS',
    settings.MANAGERS
)


"""Allowed card types - choose from 'Visa', 'MasterCard', 
   'American Express', 'Discover'."""
ALLOWED_CARD_TYPES = ('Visa', 'MasterCard') 


"""Payment backends - should be a fully qualified path, e.g. 
       
       'cart.payment.manual'

   Built in modules are in cart.payment, or you can write your own."""
PAYMENT_BACKEND = getattr(
    settings,
    'CART_PAYMENT_BACKEND',
    None
)


"""Used by payment backends to determine whether to include debugging data
   in transaction record, etc."""
PAYMENT_DEBUG = getattr(
    settings,
    'CART_PAYMENT_DEBUG',
    settings.DEBUG
)


"""Used by payment backends to log errors, warnings etc."""
LOG_DIR = getattr(
    settings,
    'CART_LOG_DIR',
    None
)


"""Webpay-specific settings."""
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


