# -*- coding: utf-8 -*-

import locale

from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from cart.utils import easy_tag
from cart import helpers
from cart.forms import AddToCartForm
from cart import helpers


register = template.Library()

locale.setlocale(locale.LC_ALL, '')

@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)



class CartNode(template.Node):
    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        context[self.varname] = helpers.get_cart()(context['request'])
        return ''

@register.tag
@easy_tag
def get_cart(_tag, _as, varname):
    """Gets the cart instance."""
    return CartNode(varname)




class AddToCartFormNode(template.Node):
    def __init__(self, *args, **kwargs):
        self.instance = template.Variable(args[1])
        self.varname = args[3]
        
        self.initial = args[4] if len(args) > 4 else kwargs.get('initial', None)
        self.single = args[5] if len(args) > 5 else kwargs.get('single', None)
        
    def render(self, context):
        if self.initial:
            initial = template.Variable(self.initial).resolve(context)
        else:
            initial = {}
        
        if self.single:
            single = template.Variable(self.single).resolve(context)
        else:
            single = False

        instance = self.instance.resolve(context)
        
        form_cls = helpers.get_add_form(instance)
        context[self.varname] = form_cls(initial=initial, single=single)
        return ''

@register.tag
@easy_tag
def get_add_to_cart_form(_tag, *args, **kwargs):
    """Gets an AddToCartForm for the specified product - e.g.
           
           {% get_add_to_cart_form for instance as varname %}
       
       """
    return AddToCartFormNode(*args, **kwargs)



@register.simple_tag
def add_to_cart_url(product):
    """Gets add-to-cart url for specified product - e.g.
           
           <form action="{% add_to_cart_url instance %}">
       """
    ctype = ContentType.objects.get_for_model(product)
    return reverse('cart.views.add', args=(ctype.id, product.id))


