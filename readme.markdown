Django-trolley is a lightweight cart system designed to 
work with a custom product catalogue app. One or more product catalogues 
can send products to the included cart via api.py; cart then takes care of 
gathering address details etc and payment.

Currently this is a work in progress.

Thanks to http://code.google.com/p/django-cart/ for inspiration.


# Requirements

* Django 1.2+ (may work on older versions too, not tested)
* simplejson
* One or more custom "product" apps - see below


# Installation

1. Run `./setup.py install` to install the cart. Alternately, you can symlink or move the `cart` directory onto your path.

2. Add `'cart'` to INSTALLED_APPS

3. Add `'cart.urls'` to your root url conf, i.e.
    
        (r'^cart/', include('cart.urls')),

4. Create templates for the cart model - you can start by copying
   the ones in `demo/templates/cart`
   
5. Define the `CART_PAYMENT_BACKEND` setting - `'cart.payment.manual'` is
   simplest.
   
6. Create a `product` model to use with your cart - typically within
   a `shop` app, but it can be anywhere. It must implement 
   `cart.models.CartProductInterface`. Alternately, copy the sample `shop` 
   app into your project and customise.
   
7. Create shop templates - samples are provided in `demo/templates/shop`


# Standalone payments

django-trolley's payment system is designed to be usable by itself for non-shop payments (donations, generic website payments etc). An example app is provided (`payment`) - to install, follow installation steps 1-4 above, and also do the following:

1. Symlink or move the `payment` directory onto your path.

2. Add `'payment'` to INSTALLED_APPS

3. Add `'payment.urls'` to your root url conf, i.e.
    
        (r'^payment/', include('payment.urls')),

4. Create a payment form template at `payment/index.html` — see the `demo/templates/payment/index.html` for an example.


# Example shop

An example shop app is provided - this can be used directly, or as a starting point for a custom shop app. Generally you'll want to write your own shop app since this one is very simple.


# Settings 

Various other settings are available for customisation - these are located and documented in the file `cart/settings.py`, but can be overridden in your project's  `settings.py` with the CART prefix. Eg

    CART_HELPER_MODULE = 'cart_helpers'


# Demo project

A demo project is provided to demonstrate the example shop and payment app working in conjunction with the cart. To run the demo:

    >> cd path-to-django-trolley/demo
    >> python manage.py syncdb
    >> python manage.py runserver


# Helper Module

Similar to django's COMMENT_APP setting, this module can be used to define custom sitewide
functionality for the cart. To use, create a module and add it to your settings, eg.

    CART_HELPER_MODULE = 'cart_helpers'

The helper module can provide any of the following:

1) A `get_cart` function, which should return a custom cart API class extending 
   cart.api.Cart. This class should override certain methods to provide custom 
   functionality. For example:

In `cart_helpers/__init__.py`:

    from cart.api import BaseCart

    class Cart(BaseCart):
        
        def shipping_cost(self):
            '''Should return total shipping cost for the cart.'''
            return 0
        
        def verify_purchase(self):
            '''Should raise a CartIntegrityError if the purchase is not allowed.'''
            return
        
        def get_available_shipping_options(self):
            '''Should return a list of shipping options for the cart, each of the form
                   
                   (key, name, choices)
                   
               where "choices" is a list of key,value pairs in the usual django format.'''
            return []
    
    def get_cart():
        return Cart

2) A `get_order_detail` function, which should return a model to be used to add custom
   data to a cart Order, similar to django's `AUTH_PROFILE_MODULE` setting. Use it for 
   adding data specific to your project, such as a separate delivery address. The model
   must have a ForeignKey to cart.Order. For example:

In `cart_helpers/__init__.py`:

    from cart_helpers.models import OrderDetail
    
    def get_order_detail():
        return OrderDetail
   
   And in `cart_helpers/models.py`:
    
    from django.db import models
    
    class OrderDetail(models.Model):
        order = models.ForeignKey('cart.Order', editable=False)
        delivery_address = models.TextField(blank=True, default='')
        
        def __unicode__(self):
            return 'Additional detail for %s' % (unicode(self.order))

   Note that in this case you'll need to add `'cart_helpers'` to your `INSTALLED_APPS` 
   setting in order for django to generate the db tables.

3) A `get_add_form` function, which takes a product instance and should return a form 
   class for adding the product to the cart. For example,
    
    from cart.forms import AddToCartForm
    
    def get_add_form(product):
        class AddForm(AddToCartForm):
            ...
        
        return AddForm
        
