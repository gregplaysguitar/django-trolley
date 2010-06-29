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
import webpay
import os
from cart.payment import PaymentException


class PaymentBackend:
    
    def makePayment(self, amount, ref, data):
    
        webpayRef = webpay.newBundle() 
        if cart_settings.PAYMENT_DEBUG:
            webpay.put(webpayRef, "DEBUG", "ON")
            webpay.put(webpayRef, "COMMENT", "Test transaction")
        else:            
            webpay.put(webpayRef, "DEBUG", "OFF")
        
        webpay.put(webpayRef, "LOGFILE", os.path.join(cart_settings.LOG_DIR, "webpay.log"))
        
        if cart_settings.WEBPAY_CLIENT_ID:
            webpay.put_ClientID(webpayRef, cart_settings.WEBPAY_CLIENT_ID)
        else:
            raise PaymentException('Payment client id not set')
        
        if cart_settings.WEBPAY_CERTIFICATE_PATH:
            webpay.put_CertificatePath(webpayRef, cart_settings.WEBPAY_CERTIFICATE_PATH)
        else:
            raise PaymentException('Webpay certificate path id not set')
        
        if cart_settings.WEBPAY_CERTIFICATE_PASSWORD:
            webpay.put_CertificatePassword(webpayRef, cart_settings.WEBPAY_CERTIFICATE_PASSWORD)
        else:
            raise PaymentException('Webpay certificate path id not set')
        
        webpay.setPort(webpayRef, "3007")
        webpay.setServers(webpayRef, "api01.buylineplus.co.nz,api02.buylineplus.co.nz")
        webpay.put(webpayRef, "INTERFACE", "CREDITCARD")
        webpay.put(webpayRef, "TRANSACTIONTYPE", "PURCHASE")
        
        webpay.put(webpayRef, "TOTALAMOUNT", "%.2f" % amount)
        webpay.put(webpayRef, "CARDDATA", str(data['number']))
        webpay.put(webpayRef, "CARDEXPIRYDATE", data['expiration'].strftime("%m%y"))
        
        success = webpay.executeTransaction( webpayRef )
        
        message = "blah blah"
        
        return success, webpay.get(webpayRef, "TXNREFERENCE" ), message 
 


 
 
    def paymentView(self, request, param, order):
        if request.POST:
            payment_form = CCForm(request.POST)
            if payment_form.is_valid():
                payment_attempt = order.paymentattempt_set.create()
                
                success, transaction_ref, message = self.makePayment(order.total(), order.pk, payment_form.cleaned_data)
                
                payment_attempt.transaction_ref = transaction_ref
                if success:
                    payment_attempt.result = "Payment successful"
                    order.payment_successful = True
                    order.save()
                else:
                    payment_attempt.result = "Payment failed"
                payment_attempt.save()
                
                
                return HttpResponseRedirect(order.get_absolute_url())
                
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
        
        
