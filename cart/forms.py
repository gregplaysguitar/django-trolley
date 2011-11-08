#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext as Context
from django.contrib.formtools.wizard import FormWizard
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms.formsets import formset_factory

import settings as cart_settings
from utils import get_order_detail_class, OrderDetailNotAvailable
from api import Cart
from models import Order

    
product_type_queryset = ContentType.objects.filter(
    reduce(Q.__or__, [Q(app_label=t[0], model=t[1]) for t in cart_settings.PRODUCT_TYPES])
)



class AddToCartForm(forms.Form):
    """A generic form for adding a product to a cart - should post to 
       cart.views.add"""
    product_type = forms.ModelChoiceField(
        queryset=product_type_queryset,
        widget=forms.widgets.HiddenInput()
    )
    product_id = forms.IntegerField(
        min_value=1,
        widget=forms.widgets.HiddenInput()
    )
    quantity = forms.IntegerField(min_value=1)


    def clean_product_id(self):
        if self.get_product():
            return self.cleaned_data['product_id']
        else:
            raise forms.ValidationError('Invalid product')
    
    def get_product(self):
        product_class = self.cleaned_data['product_type'].model_class()
        try:
            return product_class.objects.get(pk=self.cleaned_data['product_id'])
        except product_class.DoesNotExist:
            return None
        
    def get_options(self):
        options = {}
        for field in self.cleaned_data:
            if field not in ['product_id', 'product_type', 'quantity']:
                options[field] = self.cleaned_data[field]
        return options
        
    
    def get_quantity(self):
        return self.cleaned_data['quantity']
    
    def add(self, request):
        Cart(request).add(self.get_product(), self.cleaned_data['quantity'], self.get_options())
    
    
    def __init__(self, *args, **kwargs):
        single = kwargs.pop('single', False)
        product_instance = kwargs.pop('product_instance', False)
        returnval = super(AddToCartForm, self).__init__(*args, **kwargs)
        
        if single:
            self.fields['quantity'].initial = 1
            self.fields['quantity'].widget = forms.widgets.HiddenInput()
        if product_instance:
            self.fields['product_id'].initial = product_instance.id
            self.fields['product_type'].initial = ContentType.objects.get_for_model(product_instance).id
        
        return returnval



def checkout_form_factory():
    """Returns a form corresponding to a subset of the ORDER_DETAIL_MODEL, if 
       one is specified and CHECKOUT_FORM_FIELDS is set. Otherwise returns a 
       dummy form."""
    try:
        order_detail_cls = get_order_detail_class()
    except OrderDetailNotAvailable:
        order_detail_cls = None

    if order_detail_cls and cart_settings.CHECKOUT_FORM_FIELDS:
        class CheckoutForm(forms.ModelForm):
            class Meta:
                model = order_detail_cls
                fields = cart_settings.CHECKOUT_FORM_FIELDS
            
            def update(self, cart):
                for name in self.cleaned_data:
                    cart.detail_data[name] = self.cleaned_data[name]
                cart.modified()
        
        return CheckoutForm
    else:
        class DummyForm(forms.Form):
            def update(self, cart):
                pass
        return DummyForm


def shipping_options_form_factory(cart):
    """Returns a shipping options form based on the options derived
       from the cart contents."""
    class ShippingOptionsForm(forms.Form):
        def update(self, cart):
            for name in self.cleaned_data:
                cart.shipping_options[name] = self.cleaned_data[name]
            cart.modified()
            
    
    for option_tuple in cart.get_available_shipping_options():
        if option_tuple[2]:
            field = forms.ChoiceField(label=option_tuple[1], choices=option_tuple[2])
        else:
            field = forms.CharField(label=option_tuple[1])
        ShippingOptionsForm.base_fields[option_tuple[0]] = field
    
    return ShippingOptionsForm


class OrderForm(forms.ModelForm):
    """Standard order information form."""
    class Meta:
        model = Order
        fields = ('name', 'email', 'phone', 'street_address', 'suburb', 'city', 'post_code', 'country')

    def clean(self):
        if not self.cleaned_data.get('email', None) and not self.cleaned_data.get('phone', None):
            self._errors['email'] = forms.util.ErrorList(['Please enter an email address.'])
        return self.cleaned_data
    
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        for f in ('name', 'email', 'street_address', 'city', 'post_code', 'country'):
            if f in self.fields:
                self.fields[f].required = True


def order_detail_form_factory():
    """Returns a form for the extra custom details defined in ORDER_DETAIL_MODEL.
       Excludes those displayed in the checkout via CHECKOUT_FORM_FIELDS."""
    try:
        model_cls = get_order_detail_class()
        class OrderDetailForm(forms.ModelForm):
            class Meta:
                model = model_cls
                exclude = ['order'] + (cart_settings.CHECKOUT_FORM_FIELDS)
        return OrderDetailForm
    except OrderDetailNotAvailable:
        # dummy form class with no fields, to simplify the view
        class DummyForm(forms.Form):
            def __init__(self, *args, **kwargs):
                kwargs.pop('instance', None)
                super(DummyForm, self).__init__(*args, **kwargs)
        return DummyForm