from django.conf import settings

## UTIL FUNCTIONS FOR CART STUFF

"""
def cart_total(cart):
    #number of items in cart. Duplicates are counted separately.
    return sum(cart.values())

def mk_subject(text):
    return "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, text)
"""





def form_errors_as_notification(form):
    if form.errors:
        errors = []
        if '__all__' in form.errors:
            errors.append(', '.join(form.errors.pop('__all__')))
        for i in form.errors:
            errors.append("%s: %s" % (i.title(), ', '.join(form.errors[i])))
        
        return ', '.join(errors)
    else:
        return ''