# -*- coding: utf-8 -*-

import datetime

from django.contrib import admin
from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType

import helpers
import settings as cart_settings
from models import Order, OrderLine, PaymentAttempt



class PaymentAttemptInline(admin.TabularInline):
    model = PaymentAttempt
    extra = 0


class OrderLineLabelWidget(forms.widgets.HiddenInput):
    def __init__(self, attrs=None, model=None, **kwargs):
        super(OrderLineLabelWidget, self).__init__(attrs)
        self.model = model
        self.is_hidden = False
        
    def render(self, *args, **kwargs):
        if self.model:
            text_value = getattr(self.model.product, 'order_line_description', "%s: %s" % (self.model.product_content_type.app_label.title(), self.model))
        else:
            text_value = ''
        
        if self.model and hasattr(self.model.product, 'get_absolute_url'):
            return mark_safe('<a href="%s">%s</a>%s' % (self.model.product.get_absolute_url(), text_value, super(OrderLineLabelWidget, self).render(*args, **kwargs)))
        else:
            return mark_safe('<p>%s</p>%s' % (text_value, super(OrderLineLabelWidget, self).render(*args, **kwargs)))


class ReadonlyWidget(forms.widgets.HiddenInput):
    def __init__(self, *args, **kwargs):
        super(ReadonlyWidget, self).__init__(*args, **kwargs)
        self.is_hidden = False

    def render(self, name, value, **kwargs):
        original = super(ReadonlyWidget, self).render(name, value, **kwargs)
        try:
            ctype = ContentType.objects.get(pk=value)
        except ContentType.DoesNotExist:
            return original
        else:
            return mark_safe('<p>%s</p>%s' % (ctype, original))


class OrderLineForm(forms.ModelForm):
    class Meta:
        model = OrderLine
    
    def __init__(self, *args, **kwargs):
        super(OrderLineForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['product_object_id'].widget = OrderLineLabelWidget(model=kwargs.get('instance', None))
            self.fields['product_content_type'].widget = ReadonlyWidget()


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    form = OrderLineForm


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_str', 'name', 'status', 'payment_successful', 'created', 'paid', 'shipped', 'products', 'hash', )
    list_display_links = ('id', 'total_str', 'name',)
    list_filter = ('status', 'payment_successful', 'creation_date', 'completion_date')
    search_fields = ('name', 'email',)
    inlines = [OrderLineInline, PaymentAttemptInline]
    actions = ('set_status_to_shipped',)
    save_on_top = True
    
    
    def created(self, instance):
        if instance.creation_date:
            return datetime.datetime.strftime(instance.creation_date, '%Y-%m-%d')
        else:
            return 'N/A'
    created.admin_order_field = 'creation_date'
    
    def paid(self, instance):
        if instance.payment_date:
            return datetime.datetime.strftime(instance.payment_date, '%Y-%m-%d')
        else:
            return 'N/A'
    paid.admin_order_field = 'payment_date'
    
    def products(self, instance):
        products = []
        for order in instance.orderline_set.all():
            if order.product not in products:
                products.append(order.product)
            
        return ', '.join([unicode(p) for p in products])

    
    def shipped(self, instance):
        if instance.completion_date:
            return datetime.datetime.strftime(instance.completion_date, '%Y-%m-%d')
        else:
            return 'N/A'
    shipped.admin_order_field = 'completion_date'

    def set_status_to_shipped(self, request, queryset):
        for item in queryset.all():
            item.status = 'shipped'
            item.save()

order_detail = helpers.get_order_detail()
if order_detail:
    class ExtraDetailInline(admin.StackedInline):
        model = order_detail
        max_num = 1
        extra = 1
    
    OrderAdmin.inlines = [ExtraDetailInline] + OrderAdmin.inlines

admin.site.register(Order, OrderAdmin)


