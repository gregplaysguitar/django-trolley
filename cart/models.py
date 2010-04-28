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


ORDER_STATUSES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('shipped', 'Shipped'),
]


class Order(models.Model):
    hash = models.CharField(max_length=16, unique=True, editable=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(default='', blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    street_address = models.CharField(max_length=255)
    suburb = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=255)
    post_code = models.PositiveIntegerField()
    
    
    status = models.CharField(max_length=20, choices=ORDER_STATUSES, default='pending')
    payment_successful = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False, editable=False)
    acknowledgement_sent = models.BooleanField(default=False, editable=False)
    
    
    creation_date = models.DateTimeField(auto_now_add=True)
    payment_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank to auto-fill this field")
    completion_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank to auto-fill this field")
    session_id = models.CharField(max_length=32, editable=False)
    #dps_transaction_ref = models.CharField(max_length=32, blank=True)
    
    shipping_cost = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    
    class Meta:
        ordering = ('-creation_date',)
    
    def __unicode__(self):
        return "Order #%s - %s %s, %s" % (self.pk, self.first_name, self.last_name, self.total())
    
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
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        pass
    
    def __unicode__(self):
        return unicode(self.product)
        super(OrderLine, self).save()



class PaymentAttempt(models.Model):
    order = models.ForeignKey(Order)
    hash = models.CharField(max_length=16, unique=True, editable=False)
    result = models.TextField(default='', blank=True)
    
    def __unicode__(self):
        return "Payment attempt #%s on Order #%s" % (self.pk, self.order.pk)
        
        
        
def create_hash(sender, **kwargs):
    while not kwargs['instance'].hash or PaymentAttempt.objects.filter(hash=kwargs['instance'].hash).exclude(pk=kwargs['instance'].pk):
        kwargs['instance'].hash = ''.join(random.choice(string.digits + string.letters + '-_') for i in xrange(8))
models.signals.pre_save.connect(create_hash, sender=PaymentAttempt)
models.signals.pre_save.connect(create_hash, sender=Order)




