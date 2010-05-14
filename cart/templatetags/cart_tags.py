from django import template
import locale
from easy_tag import easy_tag

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
    def __init__(self, instance, varname, initial):
        self.instance = template.Variable(instance)
        self.varname = varname
        self.initial = initial
        
    def render(self, context):
        if self.initial:
            initial = dict([pair.split('=') for pair in self.initial.split(',')])
        else:
            initial = {}
        
        instance = self.instance.resolve(context)
        initial['product_type'] = ContentType.objects.get_for_model(instance).id
        initial['product_id'] = instance.id
        
        context[self.varname] = AddToCartForm(initial=initial)
        return ''

@register.tag
@easy_tag
def get_add_to_cart_form(_tag, _for, instance, _as, varname, initial=None):
    return AddToCartFormNode(instance, varname, initial)


