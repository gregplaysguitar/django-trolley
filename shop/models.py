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
        return ('shop.views.index', (self.slug,))



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
    
    def get_price(self, quantity, options={}):
        return self.price * quantity

