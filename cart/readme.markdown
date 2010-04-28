Trolley is intended to be a lightweight cart system designed to 
work with a custom product catalogue app. One or more product catalogues 
can send products to trolley via api.py; trolley then takes care of 
gathering address details etc and payment.

Currently this is a work in progress.



# Requirements

* django 1.2 (may work on older versions too)


# Product model instance requirements

* Provides `get_thumbnail(options={})` method
* Provides `get_shipping_cost(...)` (?)
* 