from django.db import models

from cart.models import DefaultCartProductInterface



class Payment(models.Model, DefaultCartProductInterface):
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    reference = models.CharField(max_length=50, blank=True)
    
    def get_price(self, quantity, options={}):
        return self.amount * quantity
    
    def __unicode__(self):
        return self.reference