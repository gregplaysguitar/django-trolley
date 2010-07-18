# -*- coding: utf-8 -*-

from django.contrib import admin
from models import Order, OrderLine, PaymentAttempt
import datetime
import settings as cart_settings
from django.db import models
from django import forms
from django.utils.safestring import mark_safe



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
            text_value = getattr(self.model, 'order_line_description', "%s: %s" % (self.model.product_content_type.app_label.title(), self.model))
        else:
            text_value = ''
        return mark_safe("<p>%s</p>%s" % (text_value, super(OrderLineLabelWidget, self).render(*args, **kwargs)))


class OrderLineForm(forms.ModelForm):
    class Meta:
        model = OrderLine
        exclude = ('product_content_type', ) 
    
    def __init__(self, *args, **kwargs):
        super(OrderLineForm, self).__init__(*args, **kwargs)
        self.fields['product_object_id'].widget = OrderLineLabelWidget(model=kwargs.get('instance', None))


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    form = OrderLineForm



class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_str', 'first_name', 'last_name', 'status', 'payment_successful', 'created', 'shipped')
    list_display_links = ('id', 'total_str', 'first_name', 'last_name',)
    list_filter = ('status', 'payment_successful', 'creation_date', 'completion_date')
    search_fields = ('first_name', 'last_name', 'email',)
    inlines = [OrderLineInline, PaymentAttemptInline]
    actions = ('set_status_to_shipped',)
    
    def created(self, instance):
        if instance.creation_date:
            return datetime.datetime.strftime(instance.creation_date, '%Y-%m-%d')
        else:
            return 'N/A'

    def shipped(self, instance):
        if instance.completion_date:
            return datetime.datetime.strftime(instance.completion_date, '%Y-%m-%d')
        else:
            return 'N/A'
    def set_status_to_shipped(self, request, queryset):
        for item in queryset.all():
            item.status = 'shipped'
            item.save()

  
if getattr(cart_settings, 'ORDER_DETAIL_MODEL', False):
    app_label, model_name = cart_settings.ORDER_DETAIL_MODEL.split('.')
    extra_detail_model = models.get_model(app_label, model_name)
    class ExtraDetailInline(admin.StackedInline):
        model = extra_detail_model
        max_num = 1
        extra = 1
    
    OrderAdmin.inlines = [ExtraDetailInline] + OrderAdmin.inlines

admin.site.register(Order, OrderAdmin)


