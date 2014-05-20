# -*- coding: utf-8 -*-
import os
import urllib, urllib2

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django import forms

import webpay

from cart.payment import PaymentException
from cart.views import steps
from cart import settings as cart_settings
from cart.payment_forms import CCForm
from cart import helpers


render_to_response = helpers.get_render_function()


class PaymentBackend(object):
    """Hosted payment system which passes credit card details to webpay for verification
    and payment. Requires webpay libraries to be installed, and the following settings:
    
        WEBPAY_CLIENT_ID
        WEBPAY_CERTIFICATE_PATH
        WEBPAY_CERTIFICATE_PASSWORD
        WEBPAY_PORT
        
    """
    
    SUCCESS_RESPONSE_CODES = ["00", "08", "77"]
    
    def makePayment(self, client_id, amount, ref, data):
        message = []
        webpayRef = webpay.newBundle() 
        if cart_settings.PAYMENT_DEBUG:
            webpay.put(webpayRef, "DEBUG", "ON")
            webpay.put(webpayRef, "COMMENT", "Test transaction")
        else:            
            webpay.put(webpayRef, "DEBUG", "OFF")
        
        webpay.put(webpayRef, "LOGFILE", os.path.join(cart_settings.LOG_DIR, "webpay.log"))
        webpay.put_ClientID(webpayRef, client_id)
        
        
        if getattr(settings, 'WEBPAY_CERTIFICATE_PATH', None):
            webpay.put_CertificatePath(webpayRef, settings.WEBPAY_CERTIFICATE_PATH)
        else:
            raise PaymentException('Webpay certificate path is not set')
        
        if getattr(settings, 'WEBPAY_CERTIFICATE_PASSWORD', None):
            webpay.put_CertificatePassword(webpayRef, settings.WEBPAY_CERTIFICATE_PASSWORD)
        else:
            raise PaymentException('Webpay certificate password is not set')
        
        if getattr(settings, 'WEBPAY_PORT', None):
            webpay.setPort(webpayRef, str(settings.WEBPAY_PORT))
        else:
            raise PaymentException('Webpay port is not set')
        
        webpay.setServers(webpayRef, "api01.buylineplus.co.nz,api02.buylineplus.co.nz")
        webpay.put(webpayRef, "INTERFACE", "CREDITCARD")
        webpay.put(webpayRef, "TRANSACTIONTYPE", "PURCHASE")
        
        tran_data = {
            'TOTALAMOUNT': "%.2f" % amount,
            'CARDDATA': str(data['number']),
            'CARDEXPIRYDATE': data['expiration'].strftime("%m%y"),
        }
        for key in tran_data:
            webpay.put(webpayRef, key, tran_data[key])
            if cart_settings.PAYMENT_DEBUG:
                message.append(key + ': ' + tran_data[key])
        
        if webpay.executeTransaction(webpayRef):
            response_data = {
                'TXNREFERENCE': webpay.get(webpayRef, "TXNREFERENCE"),
                'RESPONSECODE': webpay.get(webpayRef, "RESPONSECODE"),
                'RESPONSETEXT': webpay.get(webpayRef, "RESPONSETEXT"),
                'ERROR': webpay.get(webpayRef, "ERROR"),
                'AUTHCODE': webpay.get(webpayRef, "AUTHCODE"),
            }
            
            success = (response_data['RESPONSECODE'] in self.SUCCESS_RESPONSE_CODES)
            message.append("\n".join(["%s: %s" % (key, response_data[key]) for key in response_data]))
            user_message = webpay.get(webpayRef, "RESPONSETEXT")
            return success, response_data['TXNREFERENCE'], "\n".join(message), user_message
            
        else:
            message = "Could not communicate with the payment server"
            return False, '', message, message 
        


 
 
    def paymentView(self, request, param, order):
        error_message = ''
        
        if order.payment_successful == True:
            return HttpResponseRedirect(order.get_absolute_url())
        else:
            if request.POST:
                payment_form = CCForm(request.POST)
                if payment_form.is_valid():
                    payment_attempt = order.paymentattempt_set.create()
                    
                    client_id = getattr(settings, 'WEBPAY_CLIENT_ID', None)
                    if callable(client_id):
                        client_id = client_id(order)
                    elif not client_id:
                        raise PaymentException('Payment client id not set')
                    
                    #success, transaction_ref, message, user_message = True, 123, "test", "test user message"
                    success, transaction_ref, message, user_message = self.makePayment(client_id, order.total(), order.pk, payment_form.cleaned_data)
                    
                    payment_attempt.transaction_ref = transaction_ref
                    payment_attempt.result = message
                    payment_attempt.user_message = user_message
                    payment_attempt.success = success
                    payment_attempt.amount = order.total()
                    payment_attempt.save()
                    
                    if success:
                        order.payment_successful = True
                        order.save()
                        return HttpResponseRedirect(order.get_absolute_url())
                    else:
                        payment_form = CCForm() # don't bind data to the form since its a CC form
                        error_message = user_message
            else:
                payment_form = CCForm()
            
            
            return render_to_response(
                'cart/payment.html',
                RequestContext(request, {
                    'order': order,
                    'form': payment_form,
                    'cart': helpers.get_cart()(request),
                    'error_message': error_message,
                    'steps': steps(request),
                }),
            )
            
        
