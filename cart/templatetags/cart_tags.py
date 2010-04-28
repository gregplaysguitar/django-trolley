from django import template
import locale
from culturethree.util.decorators import easy_tag

from cart.forms import AddToCartForm
from django.contrib.contenttypes.models import ContentType

register = template.Library()


locale.setlocale(locale.LC_ALL, '')

@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)








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



"""
class CheckoutRowFormNode(template.Node):
    def __init__(self, , varname, initial):
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
"""