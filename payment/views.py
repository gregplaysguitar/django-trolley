import simplejson 

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse

from cart.forms import order_detail_form_factory

from forms import PaymentOrderForm, PaymentForm

def index(request):
    
    detail_form_cls = order_detail_form_factory()
    
    if request.POST:
        order_form = PaymentOrderForm(request.POST)
        detail_form = detail_form_cls(request.POST)
        payment_form = PaymentForm(request.POST)
        valid = order_form.is_valid()
        if valid:
            payment = payment_form.save()
            order = order_form.save()
            
            # if the form has no 'save' method, assume it's the dummy form
            if callable(getattr(detail_form, 'save', None)):
                order_detail = detail_form.save(commit=False)
                order_detail.order = order # in case it is being created for the first time
                order_detail.save()
            
            order.orderline_set.create(
                product=payment,
                quantity=1,
                price=payment.amount
            )
            order.status = 'confirmed'
            order.save()
            
            redirect_url = reverse('cart.views.payment', args=(order.hash,))
        else:
            redirect_url = None
        
        if request.is_ajax():
            html = render_to_string(
                'payment/index.inc.html',
                RequestContext(request, {
                    'order_form': order_form,
                    'detail_form': detail_form,
                    'payment_form': payment_form,
                })
            )
                
            return HttpResponse(simplejson.dumps({
                'success': valid,
                'redirect_url': redirect_url,
                'hard_redirect': True,
                'html': html,
            }), mimetype='application/json')

        elif valid:
            return HttpResponseRedirect(redirect_url)
    
    else:
        order_form = PaymentOrderForm()
        detail_form = detail_form_cls()
        payment_form = PaymentForm()
    
    return render_to_response( 'payment/index.html', {
        'order_form': order_form,
        'detail_form': detail_form,
        'payment_form': payment_form,
    }, RequestContext(request))
  

