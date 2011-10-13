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

1. Symlink or move the `cart` directory onto your path.

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
   
7. Define the `CART_PRODUCT_TYPES` setting - typically 
   
        CART_PRODUCT_TYPES = (
            ('shop', 'product'),
        )
    
8. Create shop templates - samples are provided in `demo/templates/shop`


# Demo shop

A demo shop app and templates are provided as a starting point. To use:

    >> cd demo
    >> python manage.py syncdb
    >> python manage.py runserver



# Settings 

Various other settings are available for customisation - these are 
located in the file `cart/settings` but can be overridden in your
`settings.py`




