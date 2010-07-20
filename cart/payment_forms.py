from datetime import date, datetime
from calendar import monthrange
from django import forms
import settings as cart_settings

class CreditCardField(forms.CharField):
    @staticmethod
    def get_cc_type(number):
        """
        Gets credit card type given number. Based on values from Wikipedia page
        "Credit card number".
        http://en.wikipedia.org/w/index.php?title=Credit_card_number
        """
        number = str(number)
        #group checking by ascending length of number
        if len(number) == 13:
            if number[0] == "4":
                return "Visa"
        elif len(number) == 14:
            if number[:2] == "36":
                return "MasterCard"
        elif len(number) == 15:
            if number[:2] in ("34", "37"):
                return "American Express"
        elif len(number) == 16:
            if number[:4] == "6011":
                return "Discover"
            if number[:2] in ("51", "52", "53", "54", "55"):
                return "MasterCard"
            if number[0] == "4":
                return "Visa"
        return "Unknown"
    
    def clean(self, value):
        """Check if given CC number is valid and one of the
           card types we accept"""
         
        value = value.replace('-', '').replace(' ', '')
        
        if value and (len(value) < 13 or len(value) > 16 or not value.isdigit()):
            raise forms.ValidationError('Please enter in a valid credit card number.')
        elif self.get_cc_type(value) not in cart_settings.ALLOWED_CARD_TYPES:
            raise forms.ValidationError('Please enter one of the following card types: %s' % (', '.join(cart_settings.ALLOWED_CARD_TYPES)))
            
        return super(CreditCardField, self).clean(value)


class CCExpWidget(forms.MultiWidget):
    """ Widget containing two select boxes for selecting the month and year"""
    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


class CCExpField(forms.MultiValueField):
    EXP_MONTH = [(x, x) for x in xrange(1, 13)]
    EXP_YEAR = [(x, x) for x in xrange(date.today().year,
                                       date.today().year + 15)]
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']}),
        )
        super(CCExpField, self).__init__(fields, *args, **kwargs)
        self.widget = CCExpWidget(widgets =
            [fields[0].widget, fields[1].widget])

    def clean(self, value):
        exp = super(CCExpField, self).clean(value)
        if date.today() > exp:
            raise forms.ValidationError(
            "The expiration date you entered is in the past.")
        return exp

    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


class CCForm(forms.Form):
    number = CreditCardField(
        required = True,
        label = "Card Number", 
        widget = forms.TextInput(attrs = {'maxlength': 19})
    )
    holder = forms.CharField(required = True, label = "Card Holder Name",
        max_length = 60)
    expiration = CCExpField(required = True, label = "Expiration")
    ccv_number = forms.IntegerField(required = True, label = "CCV Number",
        max_value = 9999, widget = forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        self.payment_data = kwargs.pop('payment_data', None)
        super(CCForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(CCForm, self).clean()
        if not self.errors:
            result = self.process_payment()
            if result and result[0] == 'Card declined':
                raise forms.ValidationError('Your credit card was declined.')
            elif result and result[0] == 'Processing error':
                raise forms.ValidationError(
                    'We encountered the following error while processing '+\
                    'your credit card: '+result[1])
        return cleaned

    def process_payment(self):
        if self.payment_data:
            # don't process payment if payment_data wasn't set
            datadict = self.cleaned_data
            datadict.update(self.payment_data)

            from virtualmerchant import VirtualMerchant
            vmerchant = VirtualMerchant(datadict)

            return vmerchant.process_virtualmerchant_payment()