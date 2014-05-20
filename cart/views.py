# -*- coding: utf-8 -*-

import simplejson

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.template.loader import TemplateDoesNotExist
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils import importlib
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

from api import ItemAlreadyExists
from utils import form_errors_as_notification, get_current_site
import settings as cart_settings
from models import Order
from forms import AddToCartForm, OrderForm, shipping_options_form_factory, order_detail_form_factory, checkout_form_factory
import helpers


render_to_response = helpers.get_render_function()


def index(request):
    """Dummy view for backwards-compatibility - allows reversing of cart.view.index"""
    pass
    

def validate_cart(request, view):
    cart = helpers.get_cart()(request)
    if view == 'delivery':
        return cart.is_valid()
    elif view == 'payment':
        return bool(Order.objects.filter(pk=cart.data.get('order_pk', None)).count())
    

def steps(request):
    steps = []
    
    if not cart_settings.SKIP_CHECKOUT:
        steps.append((reverse('cart.views.checkout'), 'Review Order'))
    
    for step in [
        ('delivery', 'Delivery Details'),
        ('payment', 'Payment Details')
    ]:
        if validate_cart(request, step[0]):
            steps.append((reverse('cart.views.%s' % step[0]), step[1]))
        else:
            steps.append((None, step[1]))

    return steps


@never_cache
def checkout(request):
    """Display a list of cart items, quantities, total etc, with the option
       to change quantities, specify shipping options etc."""
       
    if cart_settings.SKIP_CHECKOUT:
        return HttpResponseRedirect(reverse('cart.views.delivery'))
    else:
        cart = helpers.get_cart()(request)
        shipping_options_form_cls = shipping_options_form_factory(cart)
        checkout_form_cls = checkout_form_factory()
        
        if request.method == 'POST':
            checkout_form = checkout_form_cls(request.POST)
            shipping_options_form = shipping_options_form_cls(request.POST, prefix='shipping')
            valid = checkout_form.is_valid() and shipping_options_form.is_valid()
            
            if valid:
                cart.update_detail_data(checkout_form.cleaned_data)
                cart.update_shipping_options(shipping_options_form.cleaned_data)
                
            for item in cart:
                # update quantities if changed
                q = request.POST.get('quantity-%s' % item.formindex, None)
                if q == 'remove':
                    quantity = 0
                else:
                    try:
                        quantity = int(q)
                    except ValueError:
                        quantity = item['quantity']
                if quantity != item['quantity']:
                    cart.update(item.product, quantity, item['options'])
                    
            if request.POST.get('next', False):
                redirect_url = reverse(delivery)
            else:
                redirect_url = request.path_info
            
            if request.is_ajax():
                html = render_to_string(
                    'cart/checkout_ajax.html',
                    RequestContext(request, {
                        'cart': cart,
                        'steps': steps(request),
                        'current_step': 1,
                        'checkout_form': checkout_form,
                        'shipping_options_form': shipping_options_form,
                    })
                )
                    
                return HttpResponse(simplejson.dumps({
                    'success': valid,
                    'cart': cart.as_dict(),
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
                'steps': steps(request),
                'current_step': 1,
                'checkout_form': checkout_form,
                'shipping_options_form': shipping_options_form,
            })
        )


@never_cache
def delivery(request):
    """Collects standard delivery information, along with any extra information
       from the order_detail model."""
    
    cart = helpers.get_cart()(request)
    
    order_form_cls = helpers.get_order_form()
    detail_cls = helpers.get_order_detail()
    
    if not validate_cart(request, 'delivery'):
        return HttpResponseRedirect(reverse(checkout))
    else:
        try:
            instance = Order.objects.get(pk=cart.data.get('order_pk', None))
            if detail_cls:
                try:
                    detail_instance = instance.get_detail()
                except detail_cls.DoesNotExist:
                    detail_instance = None
            else:
                detail_instance = None
        except Order.DoesNotExist:
            instance = None
            detail_instance = None
        
        # get detail form, or dummy form if no ORDER_DETAIL_MODEL defined
        detail_form_cls = order_detail_form_factory()
        
        form_kwargs = {'label_suffix': '', 'instance': instance, 'initial': cart.data}
        detail_form_kwargs = {'label_suffix': '', 'instance': detail_instance, 'initial': cart.detail_data, 'prefix': 'detail'}
        
        
        if request.POST:
            form = order_form_cls(request.POST, **form_kwargs)
            detail_form = detail_form_cls(request.POST, **detail_form_kwargs)
            valid = form.is_valid() and detail_form.is_valid()
            if valid:
                order = form.save(commit=False)
                order.session_id = request.session.session_key
                order.shipping_cost = cart.shipping_cost()
                
                # save needed here to create the primary key
                order.save()
                
                for line in order.orderline_set.all():
                    line.delete()
                for item in cart:
                    order.orderline_set.create(
                        product=item.product,
                        quantity=item['quantity'],
                        price=item.row_total(),
                        options=simplejson.dumps(item['options'])
                    )
                
                
                # if the form has no 'save' method, assume it's the dummy form
                if callable(getattr(detail_form, 'save', None)):
                    # the detail object may have been created on order save, so check for that
                    if detail_cls:
                        try:
                            detail_form.instance = order.get_detail()
                        except detail_cls.DoesNotExist:
                            pass
                        
                    detail = detail_form.save(commit=False)
                    detail.order = order # in case it is being created for the first time
                    for field in cart_settings.CHECKOUT_FORM_FIELDS:
                        setattr(detail, field, cart.detail_data[field])
                    detail.save()
                
                # confirmed status can trigger notifications etc, so don't set it until all
                # order info is in the database
                order.status = 'confirmed'
                order.save()
               
                cart.update_data({'order_pk': order.pk})
                cart.modified()
                
                redirect_url = reverse('cart.views.payment', args=(order.hash,))
            else:
                redirect_url = None
                
            if request.is_ajax():
                html = render_to_string(
                    'cart/delivery_ajax.html',
                    RequestContext(request, {
                        'cart': cart,
                        'form': form,
                        'detail_form': detail_form,
                        'steps': steps(request),
                        'current_step': 2,
                    })
                )
                    
                return HttpResponse(simplejson.dumps({
                    'success': valid,
                    'cart': cart.as_dict(),
                    'redirect_url': redirect_url,
                    'hard_redirect': True,
                    'html': html,
                }), mimetype='application/json')

            elif valid:
                return HttpResponseRedirect(redirect_url)
                
        else:
            form = order_form_cls(**form_kwargs)
            detail_form = detail_form_cls(**detail_form_kwargs)
    
    
        return render_to_response(
            'cart/delivery.html', 
            RequestContext(request, {
                'cart': cart,
                'form': form,
                'detail_form': detail_form,
                'steps': steps(request),
                'current_step': 2,
            })
        )
    
    
    
    

@never_cache
def payment(request, order_hash=None, param=None):
    """Handle payments using the specified backend."""
    
    if order_hash:
        order = get_object_or_404(Order, hash=order_hash)
    else:
        cart = helpers.get_cart()(request)

        if not validate_cart(request, 'payment'):
            return HttpResponseRedirect(reverse('cart.views.delivery'))
        else:
            # Assume this will work since validate_cart returned True
            order = Order.objects.get(pk=cart.data['order_pk'])
            return HttpResponseRedirect(reverse('cart.views.payment', args=(order.hash,)))
        
    if order.total():
        if cart_settings.PAYMENT_BACKEND:
            try:
                backend_module = importlib.import_module(cart_settings.PAYMENT_BACKEND)
            except ImportError:
                # Try old format for backwards-compatibility
                backend_module = importlib.import_module('cart.payment.%s' % cart_settings.PAYMENT_BACKEND)
            
           
            backend = backend_module.PaymentBackend()
            
            return backend.paymentView(request, param, order)
        else:
            # If no payment backend, assume we're skipping this step 
            return HttpResponseRedirect(order.get_absolute_url())
    else:
        order.payment_successful = True
        order.save()
        return HttpResponseRedirect(order.get_absolute_url())



@never_cache
def complete(request, order_hash):
    """Display completed order information."""
    cart = helpers.get_cart()(request)
    cart.clear()
    order = get_object_or_404(Order, hash=order_hash)
    
    if not order.notification_sent:
        notify_body = render_to_string(
            'cart/email/order_notify.txt',
            RequestContext(request, {
                'order': order,
                'site': get_current_site(),
            })
        )
        send_mail(
            "Order Received",
            notify_body, 
            settings.DEFAULT_FROM_EMAIL,
            [t[1] for t in cart_settings.MANAGERS]
        )
        order.notification_sent = True
        order.save()
    
    if order.email and not order.acknowledgement_sent:
        acknowledge_body = render_to_string(
            'cart/email/order_acknowledge.txt',
            RequestContext(request, {
                'order': order,
                'site': get_current_site(),
            })
        )
        acknowledge_subject = render_to_string(
            'cart/email/order_acknowledge_subject.txt',
            RequestContext(request, {
                'order': order,
                'site': get_current_site(),
            })
        )
        try:
            acknowledge_body_html = render_to_string('cart/email/order_acknowledge.html',
                RequestContext(request, {'order': order, 'site': get_current_site()}))
        except TemplateDoesNotExist:
            acknowledge_body_html = None
        
        msg = EmailMultiAlternatives(acknowledge_subject,
                                     acknowledge_body,
                                     settings.DEFAULT_FROM_EMAIL,
                                     [order.email])
        if acknowledge_body_html:
            msg.attach_alternative(acknowledge_body_html, "text/html")
        msg.send()
        order.acknowledgement_sent = True
        order.save()
        
    return render_to_response(
        'cart/complete.html', 
        RequestContext(request, {
            'order': order,
        })
    )



def clear(request):
    """Remove all items from the cart."""
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        helpers.get_cart()(request).clear()
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
    """Update cart quantities."""
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        cart = helpers.get_cart()(request)
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


def add(request, content_type_id, product_id, form_class=None):
    """Add a product to the cart
    POST data should include content_type_id, 
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    else:
        ctype = get_object_or_404(ContentType, pk=content_type_id)
        product = get_object_or_404(ctype.model_class(), pk=product_id)
        
        if not form_class:
            form_class = helpers.get_add_form(product)
            
        form = form_class(request.POST, product=product)
        cart = helpers.get_cart()(request)

        if form.is_valid():
            form.add(request)
            notification = (messages.SUCCESS, 'Product was added to your cart. <a href="%s">View cart</a>' % (reverse(checkout)))
        else:
            notification = (messages.ERROR, 'Could not add product to cart. \r%s' % form_errors_as_notification(form))
        
        if request.is_ajax():
            data = {
                'notification': notification,
                'cart': cart.as_dict(),
                'checkout_url': reverse('cart.views.checkout'),
                'delivery_url': reverse('cart.views.delivery'),
            }
            if form.is_valid():
                data.update({
                    'success': True,
                    'cart': cart.as_dict(),
                    'product_pk': product.pk,
                    'product_name': product.name,
                    'product_quantity_added': form.get_quantity(),
                    'product_quantity': cart.get(product, form.get_options())['quantity'],
                    'total_quantity': cart.quantity(),
                })
                
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')
        else:
            messages.add_message(request, *notification)

            if form.is_valid():
                return HttpResponseRedirect(request.POST.get('redirect_to', reverse(checkout)))
            else:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse(checkout)))

