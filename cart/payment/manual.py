# -*- coding: utf-8 -*-

import urllib, urllib2

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms

from cart.payment_forms import CCForm
from cart.views import steps
from cart import helpers


class PaymentBackend(object):
    """Payment backend which saves credit card details to the database for manual processing."""
    
    def paymentView(self, request, param, order):
        if request.POST:
            payment_form = CCForm(request.POST)
            if payment_form.is_valid():
                
                payment_attempt = order.paymentattempt_set.create()
                result = "\n".join(['%s: %s' % t for t in payment_form.cleaned_data.iteritems()])

                payment_attempt.result = result
                payment_attempt.transaction_ref = "manual"
                payment_attempt.amount = order.total()
                payment_attempt.save()

                order.payment_successful = True
                order.save()
                
                return HttpResponseRedirect(order.get_absolute_url())
                
        else:
            payment_form = CCForm()
        
        
        return render_to_response(
            'cart/payment.html',
            RequestContext(request, {
                'order': order,
                'form': payment_form,
                'cart': helpers.get_cart()(request),
                'steps': steps(request),
            }),
        )
        
        
   





