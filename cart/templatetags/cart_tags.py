# -*- coding: utf-8 -*-

from django import template
import locale
from cart.utils import easy_tag

from cart.forms import AddToCartForm
from cart.api import Cart
from django.contrib.contenttypes.models import ContentType

register = template.Library()


locale.setlocale(locale.LC_ALL, '')

@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)



class CartNode(template.Node):
    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        context[self.varname] = Cart(context['request'])
        return ''

@register.tag
@easy_tag
def get_cart(_tag, _as, varname):
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
        initial['product_type'] = ContentType.objects.get_for_model(instance).id
        initial['product_id'] = instance.id
        
        context[self.varname] = AddToCartForm(initial=initial, single=single)
        return ''

@register.tag
@easy_tag
def get_add_to_cart_form(_tag, *args, **kwargs):
    return AddToCartFormNode(*args, **kwargs)


