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

    CART_ORDER_DETAIL_MODEL = 'shop.OrderDetail'


# Demo project

A demo project is provided to demonstrate the example shop and payment app working in conjunction with the cart. To run the demo:

    >> cd path-to-django-trolley/demo
    >> python manage.py syncdb
    >> python manage.py runserver




