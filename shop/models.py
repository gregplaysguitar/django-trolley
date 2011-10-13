# -*- coding: utf-8 -*-

import decimal

from django.db import models

from cart.models import CartProductInterface



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ('name', )
    
    @models.permalink
    def get_absolute_url(self):
        return ('shop.views.category', (self.category.slug, self.slug,))



class Product(models.Model, CartProductInterface):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Set to 0 for complimentary items')
        
    @models.permalink
    def get_absolute_url(self):
        return ('shop.views.product', (self.category.slug, self.slug,))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name', )
    
    @staticmethod
    def get_shipping_cost(items, cart):
        """New Zealand free
           Australia: $20.00
           Rest of the world: $50.00
        """

        if cart.shipping_options.get('location', None) == 'New Zealand':
            amount = 0
        elif cart.shipping_options.get('location', None) == 'Australia':
            amount = 20
        else:
            amount = 50
        
        return decimal.Decimal(amount)

    @staticmethod
    def get_available_shipping_options(items):
        """Returns a tuple of user-selectable shipping options"""
        return (
            ('location', 'Your location', (
                ('', 'Please Select'),
                ('New Zealand', 'New Zealand'),
                ('Australia', 'Australia'),
                ('International', 'International'),
            )),
        )
    
    @staticmethod
    def verify_purchase(items):
        pass

    def get_price(self, quantity, options={}):
        return self.price * quantity

