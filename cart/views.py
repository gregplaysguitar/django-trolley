from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import send_mail, mail_managers
from models import Order
from forms import AddToCartForm, OrderForm
from django.core.urlresolvers import reverse
from api import Cart, ItemAlreadyExists
import simplejson
from utils import form_errors_as_notification
from django.contrib import messages
import settings as cart_settings
from django.utils import importlib



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


def checkout(request):
    cart = Cart(request)
    if request.method == 'POST':
        for item in cart:
            index = 'quantity-%s' % unicode(item.formindex())
            try:
                quantity = int(request.POST.get(index, item['quantity']))
                cart.update(item.product, quantity, item['options'])
            except ValueError:
                pass
        if not request.is_ajax():
            return HttpResponseRedirect(request.path_info)
    
    if request.is_ajax():
        template = 'cart/checkout_ajax.html'
    else:
        template = 'cart/checkout.html'
    
    return render_to_response(
        template,
        RequestContext(request, {
            'cart': cart,
            'steps': steps(),
            'current_step': 1,
        })
    )


def delivery(request):
    cart = Cart(request)
    
    if not cart.is_valid():
        return HttpResponseRedirect(reverse(checkout))
    
    try:
        instance = Order.objects.get(pk=cart.data.get('order_pk', None))
    except Order.DoesNotExist:
        instance = None
    
    if request.POST:
        form = OrderForm(request.POST, label_suffix='', instance=instance)
        if form.is_valid():
            order = form.save(commit=False)
            order.session_id = request.session.session_key
            order.shipping_cost = cart.shipping_cost()
            
            order.save()
            
            cart.data['order_pk'] = order.pk
            cart.modified()
            return HttpResponseRedirect(reverse('cart.views.payment'))
            
            """
            cart.clear()
            """
    else:
        form = OrderForm(label_suffix='', instance=instance)
    
    return render_to_response(
        'cart/delivery.html', 
        RequestContext(request, {
            'cart': cart,
            'form': form,
            'steps': steps(),
            'current_step': 2,
        })
    )

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
        )
    order.status = 'confirmed'
    order.save()
    
    if cart_settings.PAYMENT_BACKEND.find('.') == -1:
        print 'cart.payment.%s' % cart_settings.PAYMENT_BACKEND
        backend_module = importlib.import_module('cart.payment.%s' % cart_settings.PAYMENT_BACKEND)
    else:
        backend_module = importlib.import_module(cart_settings.PAYMENT_BACKEND)
    
   
    backend = backend_module.PaymentBackend()
    
    return backend.paymentView(request, param, order)
    
    
    """
    return render_to_response(
        'cart/payment.html', 
        RequestContext(request, {
            'steps': steps(),
            'current_step': 3,
        })
    )
    """


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
                mail_managers("Order Received", notify_body)
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
            return HttpResponseRedirect(request.POST.get('redirect_to', reverse(index)))
  

def add(request, form_class=AddToCartForm):
    """add a product to the cart
    POST data should include content_type_id, 
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET not allowed; POST is required.')
    else:
        form = form_class(request.POST)
        if form.is_valid():
            try:
                form.add(request)
                notification = (messages.SUCCESS, 'Product added to cart. <a href="%s">View cart</a>' % (reverse(index)))
            except ItemAlreadyExists:
                notification = (messages.ERROR, 'Item is already in your cart. <a href="%s">View cart</a>' % (reverse(index)))
        else:
            notification = (messages.ERROR, 'Could not add product to cart. %s' % form_errors_as_notification(form))
                    
        
        
        if request.is_ajax():
            response = HttpResponse()
            
            cart = Cart(request)
            
            if form.is_valid():
                data = {
                    'notification': notification,
                    'product_pk': form.get_product().pk,
                    'product_name': form.get_product().name,
                    'product_quantity_added': form.get_quantity(),
                    'product_quantity': cart.get(form.get_product(), form.get_options())['quantity'],
                    'checkout_url': reverse('cart.views.checkout'),
                    'cart_url': reverse('cart.views.index'),
                    #'cart_count': cart.total(),
                }
            else:
                data = {}
               
            response.write(simplejson.dumps(data))
                
            return response
        else:
            messages.add_message(request, *notification)

            if form.is_valid():
                return HttpResponseRedirect(request.POST.get('redirect_to', reverse(index)))
            else:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse(index)))

