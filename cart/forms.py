from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext as Context
from django.contrib.formtools.wizard import FormWizard
from models import Order
from datetime import datetime
from decimal import Decimal

from cart import settings as cart_settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from api import Cart
from django.forms.formsets import formset_factory


    
product_type_queryset = ContentType.objects.filter(
    reduce(Q.__or__, [Q(app_label=t[0], model=t[1]) for t in cart_settings.PRODUCT_TYPES])
)

class AddToCartForm(forms.Form):
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
        # TODO
        return {}    
    
    def get_quantity(self):
        return self.cleaned_data['quantity']
    
    def add(self, request):
        Cart(request).add(self.get_product(), self.cleaned_data['quantity'])
    
    
    def __init__(self, *args, **kwargs):
        single = kwargs.pop('single', False)
        returnval = super(AddToCartForm, self).__init__(*args, **kwargs)

        if single:
            self.fields['quantity'].initial = 1
            self.fields['quantity'].widget = forms.widgets.HiddenInput()
            
        return returnval


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb', 'city', 'post_code')

    def clean(self):
        if not self.cleaned_data.get('email', None) and not self.cleaned_data.get('phone', None):
            self._errors['email'] = forms.util.ErrorList(['Please enter a phone number or an email address.'])
        return self.cleaned_data

OrderForm.base_fields['suburb'].required = False
