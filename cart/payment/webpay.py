from django.conf import settings
import urllib, urllib2
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django import forms
from cart import settings as cart_settings
from cart.payment_forms import PaymentForm
from cart.api import Cart




class PaymentBackend:
    
    def paymentView(self, request, param, order):
        if request.POST:
            payment_form = PaymentForm(request.POST)
            if payment_form.is_valid():
                payment_attempt = order.paymentattempt_set.create()
                payment_attempt.result = "RESULT HERE"
                payment_attempt.save()
                    
                order.payment_successful = True
                order.transaction_ref = "REF HERE"
                order.save()
                
                return HttpResponseRedirect(order.get_absolute_url())
                
        else:
            payment_form = PaymentForm()
        
        
        return render_to_response(
            'cart/payment.html',
            RequestContext(request, {
                'order': order,
                'form': payment_form,
                'cart': Cart(request),
            }),
        )
        
        
   





