from django.conf import settings

## UTIL FUNCTIONS FOR CART STUFF

"""
def cart_total(cart):
    #number of items in cart. Duplicates are counted separately.
    return sum(cart.values())

def mk_subject(text):
    return "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, text)
"""





def form_errors_as_notification(error_list):
    errors = []
    if '__all__' in error_list:
        errors.append(', '.join(error_list.pop('__all__')))
    for i in error_list:
        errors.append("%s: %s" % (i.title(), ', '.join(error_list[i])))
    
    return ', '.join(errors)