# -*- coding: utf-8 -*-

from django.conf import settings
import urllib, urllib2
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django import forms
from cart import settings as cart_settings
from cart.payment_forms import CCForm
from cart.api import Cart




class PaymentBackend:
    
    def paymentView(self, request, param, order):
        if request.POST:
            payment_form = CCForm(request.POST)
            if payment_form.is_valid():
                
                #{'ccv_number': 123, 'holder': u'123', 'number': 4111111111111111L, 'expiration': datetime.date(2012, 1, 31)}
            
                payment_attempt = order.paymentattempt_set.create()
                result = "\n".join(['%s: %s' % t for t in payment_form.cleaned_data.iteritems()])

                print result
                
                payment_attempt.result = result
                payment_attempt.transaction_ref = "manual"
                payment_attempt.amount = order.total()
                payment_attempt.save()
                    

                order.payment_successful = True
                order.save()
                
                #return HttpResponseRedirect(order.get_absolute_url())
                
        else:
            payment_form = CCForm()
        
        
        return render_to_response(
            'cart/payment.html',
            RequestContext(request, {
                'order': order,
                'form': payment_form,
                'cart': Cart(request),
            }),
        )
        
        
   




