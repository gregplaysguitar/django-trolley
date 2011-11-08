from django import forms

from cart.forms import OrderForm

from models import Payment



class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        
        
class PaymentOrderForm(OrderForm):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    
    class Meta(OrderForm.Meta):
        fields = ('name', 'email', 'phone')
        