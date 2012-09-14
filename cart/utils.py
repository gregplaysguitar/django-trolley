from django.conf import settings
from django.db import models
from django import template
from django.contrib.sites.models import Site

import settings as cart_settings


def get_current_site():
    try:
        return Site.objects.get_current()
    except Site.DoesNotExist:
        return None


def form_errors_as_notification(form):
    """Display form errors in plain text format, for display via ajax."""
    if form.errors:
        errors = []
        if '__all__' in form.errors:
            errors.append(', '.join(form.errors.pop('__all__')))
        for i in form.errors:
            errors.append("%s: %s" % (i.replace('_', ' ').title(), ', '.join(form.errors[i])))
        
        return '\r'.join(errors)
    else:
        return ''


def easy_tag(func):
    """Deal with the repetitive parts of parsing template tags."""
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


def get_product_types():
    from models import CartProductInterface
    return [cls for cls in models.get_models() if issubclass(cls, CartProductInterface)]
