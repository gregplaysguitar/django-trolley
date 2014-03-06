import os

from django.conf import settings


if getattr(settings, 'CART_ORDER_DETAIL_MODEL', None):
    raise DeprecationWarning('The CART_ORDER_DETAIL_MODEL setting is deprecated; use a HELPER_MODULE instead.')


"""A module to provide custom functionality not specific to a product model, eg shipping
calculations."""
HELPER_MODULE = getattr(
    settings,
    'CART_HELPER_MODULE',
    None
)


"""List of fields to show in the checkout form, eg discount code - 
   must correpond to fields in the order detail model class. Fields
   in the detail class but not listed here will show on the 
   delivery details page."""
# TODO make this a function in the HELPER_MODULE
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
   'American Express', 'Discover', 'Diners Club'."""
ALLOWED_CARD_TYPES = getattr(
    settings,
    'CART_ALLOWED_CARD_TYPES',
    ('Visa', 'MasterCard') 
)

"""Payment backends - should be a fully qualified path, e.g. 
       
       'cart.payment.manual'

   Built in modules are in cart.payment, or you can write your own. If set to
   None, the payment step will be skipped and the user will go straight to
   the order complete page, which can contain payment instructions."""
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

TEMPLATE_RENDERER = getattr(settings, 'CART_TEMPLATE_RENDERER', 
                            'django.shortcuts.render_to_response')
