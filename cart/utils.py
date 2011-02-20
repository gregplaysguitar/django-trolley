from django.conf import settings
import settings as cart_settings
from django.db import models
from django import template


## UTIL FUNCTIONS FOR CART STUFF

"""
def cart_total(cart):
    #number of items in cart. Duplicates are counted separately.
    return sum(cart.values())

def mk_subject(text):
    return "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, text)
"""


class OrderDetailNotAvailable(Exception):
    pass



def form_errors_as_notification(form):
    if form.errors:
        errors = []
        if '__all__' in form.errors:
            errors.append(', '.join(form.errors.pop('__all__')))
        for i in form.errors:
            errors.append("%s: %s" % (i.replace('_', ' ').title(), ', '.join(form.errors[i])))
        
        return ', '.join(errors)
    else:
        return ''
        


def get_order_detail_class():
    if not getattr(cart_settings, 'ORDER_DETAIL_MODEL', False):
        raise OrderDetailNotAvailable
    else:
        try:
            app_label, model_name = cart_settings.ORDER_DETAIL_MODEL.split('.')
            return models.get_model(app_label, model_name)
        except (ImportError):
            raise OrderDetailNotAvailable





def easy_tag(func):
    """deal with the repetitive parts of parsing template tags"""
    def inner(parser, token):
        # divide token into args and kwargs
        args = []
        kwargs = {}
        for arg in token.split_contents():
            try:
                name, value = arg.split('=')
                kwargs[str(name)] = value
            except ValueError:
                args.append(arg)
        try:
            # try passing parser as a kwarg for tags that support it
            extrakwargs = kwargs.copy()
            extrakwargs['parser'] = parser
            return func(*args, **extrakwargs)
        except TypeError:
            # otherwise just send through the original args and kwargs
            try:
                return func(*args, **kwargs)
            except TypeError, e:
                raise template.TemplateSyntaxError('Bad arguments for tag "%s"' % args[0])
    inner.__name__ = func.__name__
    inner.__doc__ = inner.__doc__
    return inner


