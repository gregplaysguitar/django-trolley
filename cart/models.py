# -*- coding: utf-8 -*-


#from django.utils.translation import ugettext_lazy as _
from django.db import models
#from django.conf import settings
#from tagging.fields import TagField
#from django.db.models import permalink

#import copy
#from decimal import Decimal
import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import string, random
import decimal
from utils import get_order_detail_class, OrderDetailNotAvailable
import settings as cart_settings


# Any items to be added to the cart must implement the following interface.
# CartProductInterface is the minimal one; it does nothing.
# DefaultCartProductInterface implements sensible defaults.






class CartProductInterface(object):
    """Minimal CartProductInterface implementation, raising NotImplementedError
    for all required methods."""
    def get_thumbnail(self, options={}):
        raise NotImplementedError()

    def get_price(self, quantity, options={}):
        raise NotImplementedError()

    @staticmethod
    def get_shipping_cost(items, options={}):
        raise NotImplementedError()
    
    @staticmethod
    def get_available_shipping_options(items):
        raise NotImplementedError()
    
    @staticmethod
    def verify_purchase(items):
        raise NotImplementedError()

class DefaultCartProductInterface(CartProductInterface):
    """CartProductInterface interface implementation, giving sensible defaults for
    all required methods."""
    def get_thumbnail(self, options={}):
        return None

    @staticmethod
    def get_shipping_cost(items, options={}):
        return 0

    @staticmethod
    def get_available_shipping_options(items):
        return None
        
    @staticmethod
    def verify_purchase(items):
        return True





class Order(models.Model):
    hash = models.CharField(max_length=16, unique=True, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(default='', blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    street_address = models.CharField(max_length=255)
    suburb = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=255)
    post_code = models.PositiveIntegerField(max_length=20)
    country = models.CharField(max_length=255)
    
    
    status = models.CharField(max_length=20, choices=cart_settings.ORDER_STATUSES, default='pending')
    payment_successful = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False, editable=False)
    acknowledgement_sent = models.BooleanField(default=False, editable=False)
    
    
    creation_date = models.DateTimeField(auto_now_add=True)
    payment_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank to auto-fill this field")
    completion_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank to auto-fill this field")
    session_id = models.CharField(max_length=32, editable=False)
    
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    
    
    class Meta:
        ordering = ('-creation_date',)
    
    def __unicode__(self):
        return "Order #%s - %s, %s" % (self.pk, self.name, self.total())
    
    def save(self):
        if (not self.completion_date) and self.status == 'shipped':
            self.completion_date = datetime.datetime.now()
        if (not self.payment_date) and self.payment_successful:
            self.payment_date = datetime.datetime.now()
        
        super(Order, self).save()

    
    def total(self):
        return sum(line.price for line in self.orderline_set.all()) + self.shipping_cost
        
    def total_str(self, prefix='$'):
        return "%s%.2f" % (prefix, self.total())
    total_str.short_description = "Total"
    
    def total_quantity(self):
        return sum(line.quantity for line in self.orderline_set.all())
    
    @models.permalink
    def get_absolute_url(self):
        return ('cart.views.complete', (self.hash,))
    
    @models.permalink
    def get_admin_url(self):
        return ('admin:cart_order_change', (self.pk,))

    
    def get_detail(self):
        """
        Returns extra detail as stored in the ORDER_DETAIL_MODEL setting
        """
        if not hasattr(self, '_detail_cache'):
            try:
                self._detail_cache = get_order_detail_class()._default_manager.using(self._state.db).get(order__id__exact=self.id)
                self._detail_cache.order = self
            except OrderDetailNotAvailable:
                self._detail_cache = None
        return self._detail_cache
    
    
    """
    def has_shipped(self):
        return bool(self.shipped)
    has_shipped.boolean = True
    has_shipped.short_description = 'Shipped'
    has_shipped.admin_order_field = 'shipped'
    
    def shipping_cost(self):
        return Decimal(str(SHIP_BASE)) + Decimal(self.shipping_base) + sum(line.shipping_cost() for line in self.orderline_set.all())

    def shipping_cost_str(self, prefix='$'):
        return u"%s%.2f" % (prefix, self.shipping_cost())
    
    """

class OrderLine(models.Model):
    order = models.ForeignKey(Order)
    
    product_content_type = models.ForeignKey(ContentType)
    product_object_id = models.PositiveIntegerField()
    product = generic.GenericForeignKey('product_content_type', 'product_object_id')    

    quantity = models.IntegerField(default=1)
    # total price for the line, not per-unit
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        pass
    
    def __unicode__(self):
        return unicode(self.product)
        super(OrderLine, self).save()
    
    def latest_payment_attempt(self):
        if self.payment_attempt_set.count():
            return self.payment_attempt_set.order_by('-creation_date')[0]
        else:
            return None

class PaymentAttempt(models.Model):
    order = models.ForeignKey(Order)
    hash = models.CharField(max_length=16, unique=True, editable=False)
    result = models.TextField(default='', blank=True)
    user_message = models.TextField(default='', blank=True)
    transaction_ref = models.CharField(max_length=32, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    success = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "Payment attempt #%s on Order #%s" % (self.pk, self.order.pk)
    
    class Meta:
        ordering = ('-creation_date',)
        
        
def create_hash(sender, **kwargs):
    while not kwargs['instance'].hash or PaymentAttempt.objects.filter(hash=kwargs['instance'].hash).exclude(pk=kwargs['instance'].pk):
        hash = ''.join(random.choice(string.digits + string.letters) for i in xrange(8))
        kwargs['instance'].hash = hash
models.signals.pre_save.connect(create_hash, sender=PaymentAttempt)
models.signals.pre_save.connect(create_hash, sender=Order)




