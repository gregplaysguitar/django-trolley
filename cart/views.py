# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import send_mail, mail_managers
from models import Order
from forms import AddToCartForm, OrderForm, shipping_options_form_factory, order_detail_form_factory, checkout_form_factory
from django.core.urlresolvers import reverse
from api import Cart, ItemAlreadyExists
import simplejson
from utils import form_errors_as_notification, get_order_detail_class
from django.contrib import messages
import settings as cart_settings
from django.utils import importlib
from django.views.decorators.cache import never_cache


def index(request):
    return HttpResponseRedirect(reverse(checkout))
    
    """
    if request.is_ajax():
        template = 'cart/index_ajax.html',
    else:
        template = 'cart/index.html',
        
    cart = Cart(request)
            
    return render_to_response(
        template, 
        RequestContext(request, {
            'cart': cart,
        })
    )
    """

def steps():
    return (
        (reverse('cart.views.checkout'), 'Review Order'),
        (reverse('cart.views.delivery'), 'Delivery Details'),
        (reverse('cart.views.payment'), 'Payment Details'), 
    )


@never_cache
def checkout(request):
    if cart_settings.SKIP_CHECKOUT:
        return HttpResponseRedirect(steps()[1][0])
    else:
        cart = Cart(request)
        shipping_options_form_cls = shipping_options_form_factory(cart)
        checkout_form_cls = checkout_form_factory()
        
        if request.method == 'POST':
            checkout_form = checkout_form_cls(request.POST)
            shipping_options_form = shipping_options_form_cls(request.POST, prefix='shipping')
            valid = checkout_form.is_valid() and shipping_options_form.is_valid()
            
            if valid:
                checkout_form.update(cart)
                shipping_options_form.update(cart)
            
            for item in cart:
                index = 'quantity-%s' % unicode(item.formindex)
                try:
                    if str(request.POST.get(index, None)).lower() == 'remove':
                        quantity = 0
                    else:
                        quantity = int(request.POST.get(index, item['quantity']) or 0)
                    cart.update(item.product, quantity, item['options'])
                except ValueError:
                    pass
                    
          
            if request.POST.get('next', False):
                redirect_url = reverse(delivery)
            else:
                redirect_url = request.path_info
            
            if request.is_ajax():
                html = render_to_string(
                    'cart/checkout_ajax.html',
                    RequestContext(request, {
                        'cart': cart,
                        'steps': steps(),
                        'current_step': 1,
                        'checkout_form': checkout_form,
                        'shipping_options_form': shipping_options_form,
                    })
                )
                    
                return HttpResponse(simplejson.dumps({
                    'success': valid,
                    'redirect_url': redirect_url if valid else None,
                    'html': html,
                }), mimetype='application/json')

            elif valid:
                return HttpResponseRedirect(redirect_url)
        else:
            checkout_form = checkout_form_cls(initial=cart.detail_data)
            shipping_options_form = shipping_options_form_cls(prefix='shipping', initial=cart.shipping_options)

        
        return render_to_response(
            'cart/checkout.html',
            RequestContext(request, {
                'cart': cart,
                'steps': steps(),
                'current_step': 1,
                'checkout_form': checkout_form,
                'shipping_options_form': shipping_options_form,
            })
        )


@never_cache
def delivery(request):
    cart = Cart(request)
    
    if not cart.is_valid():
        return HttpResponseRedirect(reverse(checkout))
    else:
        try:
            instance = Order.objects.get(pk=cart.data.get('order_pk', None))
            try:
                detail_instance = instance.get_detail()
            except get_order_detail_class().DoesNotExist:
                detail_instance = None
        except Order.DoesNotExist:
            instance = None
            detail_instance = None
        
        # get detail form, or dummy form if no ORDER_DETAIL_MODEL defined
        detail_form_cls = order_detail_form_factory()
        
        form_kwargs = {'label_suffix': '', 'instance': instance, 'initial': cart.data}
        detail_form_kwargs = {'label_suffix': '', 'instance': detail_instance, 'initial': cart.detail_data, 'prefix': 'detail'}
        
        
        if request.POST:
            form = OrderForm(request.POST, **form_kwargs)
            detail_form = detail_form_cls(request.POST, **detail_form_kwargs)
            valid = form.is_valid() and detail_form.is_valid()
            if valid:
                order = form.save(commit=False)
                order.session_id = request.session.session_key
                order.shipping_cost = cart.shipping_cost()
                order.save()
                
                # if the form has no 'save' method, assume it's the dummy form
                if callable(getattr(detail_form, 'save', None)):
                    detail = detail_form.save(commit=False)
                    detail.order = order # in case it is being created for the first time
                    for field in cart_settings.CHECKOUT_FORM_FIELDS:
                        setattr(detail, field, cart.detail_data[field])
                    detail.save()
                    
                
                cart.data['order_pk'] = order.pk
                cart.modified()
                
                
            redirect_url = reverse('cart.views.payment')
            
            if request.is_ajax():
                html = render_to_string(
                    'cart/delivery_ajax.html',
                    RequestContext(request, {
                        'cart': cart,
                        'form': form,
                        'detail_form': detail_form,
                        'steps': steps(),
                        'current_step': 2,
                    })
                )
                    
                return HttpResponse(simplejson.dumps({
                    'success': valid,
                    'redirect_url': redirect_url if valid else None,
                    'hard_redirect': True,
                    'html': html,
                }), mimetype='application/json')

            elif valid:
                return HttpResponseRedirect(redirect_url)
                
        else:
            form = OrderForm(**form_kwargs)
            detail_form = detail_form_cls(**detail_form_kwargs)
    
    
        return render_to_response(
            'cart/delivery.html', 
            RequestContext(request, {
                'cart': cart,
                'form': form,
                'detail_form': detail_form,
                'steps': steps(),
                'current_step': 2,
            })
        )
    
    
    
    

@never_cache
def payment(request, param=None):
    cart = Cart(request)

    try:
        order = Order.objects.get(pk=cart.data.get('order_pk', None))
    except Order.DoesNotExist:
        return HttpResponseRedirect(reverse('cart.views.checkout'))
    
    for line in order.orderline_set.all():
        line.delete()
    for item in cart:
        order.orderline_set.create(
            product=item.product,
            quantity=item['quantity'],
            price=item.row_total(),
            options=simplejson.dumps(item['options'])
        )
    order.status = 'confirmed'
    order.save()
    
    if order.total():
        try:
            backend_module = importlib.import_module('cart.payment.%s' % cart_settings.PAYMENT_BACKEND)
        except ImportError:
            backend_module = importlib.import_module(cart_settings.PAYMENT_BACKEND)
        
       
        backend = backend_module.PaymentBackend()
        
        return backend.paymentView(request, param, order)
    else:
        order.payment_successful = True
        order.save()
        return HttpResponseRedirect(order.get_absolute_url())
    


@never_cache
def complete(request, order_hash):
    cart = Cart(request)
    cart.clear()
    order = get_object_or_404(Order, hash=order_hash)
    
    if (not order.notification_sent or not order.acknowledgement_sent) and order.payment_successful:
        acknowledge_body = render_to_string('cart/email/order_acknowledge.txt',
            RequestContext(request, {'order': order}))
        acknowledge_subject = render_to_string('cart/email/order_acknowledge_subject.txt',
                RequestContext(request, {'order': order}))

        notify_body = render_to_string('cart/email/order_notify.txt',
            RequestContext(request, {'order': order}))

        def TMP_send_messages():
            if order.email and not order.acknowledgement_sent:
                send_mail(
                    acknowledge_subject,
                    acknowledge_body, 
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email]
                )
            if not order.notification_sent:
                send_mail(
                    "Order Received",
                    notify_body, 
                    settings.DEFAULT_FROM_EMAIL,
                    [t[1] for t in cart_settings.MANAGERS]
                )
            order.save()
         
        #run_async(TMP_send_messages)
        TMP_send_messages()
        order.notification_sent = True
        order.acknowledgement_sent = True
        order.save()
        
    return render_to_response(
        'cart/complete.html', 
        RequestContext(request, {
            'order': order,
        })
    )



def clear(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        Cart(request).clear()
        notification = (messages.SUCCESS, 'Your cart was emptied',)
        
        if request.is_ajax():
            response = HttpResponse()
            response.write(simplejson.dumps({
                'notification': notification
            }))
            return response
        else:
            messages.add_message(request, *notification)
            return HttpResponseRedirect(request.POST.get('redirect_to', reverse(checkout)))
  


@never_cache
def update(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        cart = Cart(request)
        for item in cart:
            index = 'quantity-%s' % unicode(item.formindex)
            if index in request.POST:
                try:
                    quantity = int(request.POST[index])
                    cart.update(item.product, quantity, item['options'])
                except ValueError:
                    pass
        
        notification = (messages.SUCCESS, 'Cart updated. <a href="%s">View cart</a>' % (reverse(checkout)))
        
        if request.is_ajax():
            response = HttpResponse()
            
            data = {
                'cart': cart.as_dict(),
                'notification': notification,
            }
               
            response.write(simplejson.dumps(data))
                
            return response
        else:
            messages.add_message(request, *notification)
            return HttpResponseRedirect(request.POST.get('redirect_to', reverse(checkout)))


    


def add(request, form_class=AddToCartForm):
    """add a product to the cart
    POST data should include content_type_id, 
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        form = form_class(request.POST)
        cart = Cart(request)

        if form.is_valid():
            form.add(request)
            notification = (messages.SUCCESS, 'Product was added to your cart. <a href="%s">View cart</a>' % (reverse(checkout)))
        else:
            notification = (messages.ERROR, 'Could not add product to cart. %s' % form_errors_as_notification(form))
                    
        
        
        if request.is_ajax():
            data = {
                'notification': notification,
                'cart': cart.as_dict(),
                'checkout_url': reverse('cart.views.checkout'),
                'cart_url': reverse('cart.views.index'),
            }
            if form.is_valid():
                data.update({
                    'success': True,
                    'product_pk': form.get_product().pk,
                    'product_name': form.get_product().name,
                    'product_quantity_added': form.get_quantity(),
                    'product_quantity': cart.get(form.get_product(), form.get_options())['quantity'],
                })
                
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')
        else:
            messages.add_message(request, *notification)

            if form.is_valid():
                return HttpResponseRedirect(request.POST.get('redirect_to', reverse(checkout)))
            else:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse(checkout)))

