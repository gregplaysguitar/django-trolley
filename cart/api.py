# -*- coding: utf-8 -*-

import pickle
from django.contrib.contenttypes.models import ContentType
from UserDict import DictMixin
import hashlib
import decimal


CART_INDEX = 'cart'

class ItemAlreadyExists(Exception):
    pass

class ItemDoesNotExist(Exception):
    pass
    
class ItemIntegrityError(Exception):
    pass
    
class CartIntegrityError(Exception):
    pass


def create_cart_index(product, options):
    return (ContentType.objects.get_for_model(product).pk, 
            product.pk,
            pickle.dumps(options))







class Item(DictMixin):
    def __init__(self, data, cart):
        self.data = {'options': {}}
        self.cart = cart
        for key in ('product_pk', 'quantity', 'product_content_type_id'):
            if not key in data:
                raise ItemIntegrityError
        
        try:
            data['quantity'] = int(data['quantity'])
        except TypeError:
            raise CartIntegrityError('Quantity must be a positive integer.')
        
        try:
            model_class = ContentType.objects.get(pk=data['product_content_type_id']).model_class()
        except (ContentType.DoesNotExist):
            raise CartIntegrityError('Product type is not valid.')
        
        try:
            model_class.objects.get(pk=data['product_pk'])
        except model_class.DoesNotExist:
            raise CartIntegrityError('Product does not exist.')
        
        self.data.update(data)
        
    def __getitem__(self, key):
        return self.data.__getitem__(key)
 
    def __setitem__(self, key, item):
        return self.data.__setitem__(key, item)
 
    def __delitem__(self, key):
        return self.data.__delitem__(key)
 
    def keys(self):
        return self.data.keys()

    @property
    def product(self):
        if not self._product:
            ctype = ContentType.objects.get(pk=self.data['product_content_type_id']).model_class()
            self._product = ctype.objects.get(pk=self.data['product_pk'])
        return self._product
    _product = None
    
    
    def original_row_total(self):
        if not self._original_row_total:
            self._original_row_total = self.product.get_price(self.get('quantity', 0), self['options'])
        return self._original_row_total
    _original_row_total = None
    
    def row_total(self):
        if not self._row_total:
            if hasattr(self.product, 'get_discounted_price'):
                self._row_total = self.product.get_discounted_price(self.get('quantity', 0), self['options'], self.cart)
            else:
                self._row_total = self.original_row_total()
        return self._row_total
    _row_total = None
    
    def ctype(self):
        if not self._ctype:
            self._ctype = ContentType.objects.get_for_model(self.product)
        return self._ctype
    _ctype = None
    
    def createindex(self):
        return create_cart_index(self.product, self['options'])
    
    def formindex(self):
        return hashlib.md5(unicode(self.createindex())).hexdigest()

    def options_text(self):
        return ", ".join([self['options'][key] for key in self['options']])
    
    
class Cart:
    def __init__(self, request):
        if not request.session.get(CART_INDEX, False):
            request.session[CART_INDEX] = {}
        if not request.session[CART_INDEX].get('lines'):
            request.session[CART_INDEX]['lines'] = {}
        if not request.session[CART_INDEX].get('data'):
            request.session[CART_INDEX]['data'] = {}
        if not request.session[CART_INDEX].get('detail_data'):
            request.session[CART_INDEX]['detail_data'] = {}
        if not request.session[CART_INDEX].get('shipping_options'):
            request.session[CART_INDEX]['shipping_options'] = {}
        
        self.lines = request.session[CART_INDEX]['lines']
        self.data = request.session[CART_INDEX]['data']
        self.detail_data = request.session[CART_INDEX]['detail_data']
        self.shipping_options = request.session[CART_INDEX]['shipping_options']
        self.session = request.session
    
    def __iter__(self):
        keys = self.lines.keys()
        keys.sort()
        
        for item in map(self.lines.get, keys):
            try:
                yield item
            except ItemIntegrityError:
                pass

    
    def ctype_list(self):
        list = []
        for item in self:
            ctype = item.ctype()
            if not ctype in list:
                list.append(ctype)
        return list
    
    def add(self, product, quantity=1, options={}):
        item = Item({
            'product_pk': product.pk,
            'product_content_type_id': ContentType.objects.get_for_model(product).pk,
            'options': options,
            'quantity': quantity
        }, self)
        index = item.createindex()
        if not self.lines.get(index, False):
            self.lines[index] = item
            self.modified()
        else:
            raise ItemAlreadyExists
            
    def remove(self, *args):
        if isinstance(args[0], Item):
            product = args[0].product
            options = args[0]['options']
        else:
            product = args[0]
            options = len(args) > 1 and args[1] or {}
            
        index = create_cart_index(product, options)
        if self.lines.get(index, False):
            del(self.lines[index])
            self.modified()
        else:
            raise ItemDoesNotExist

    def update(self, product, quantity, options={}):
        q = int(quantity or 0)
        try:
            if q:
                self.lines[create_cart_index(product, options)]['quantity'] = q
            else:
                self.remove(product, options)
            self.modified()
        except IndexError:
            raise ItemDoesNotExist
    
    def modified(self):
        self.session.modified = True
    
    def get(self, product, options={}):
        return Item(self.lines[create_cart_index(product, options)], cart)
    
    def clear(self):
        for index in self.lines.keys():
            del(self.lines[index])
        for index in self.data.keys():
            del(self.data[index])
        self.modified()
        
    
    def quantity(self):
        return sum([item.get('quantity', 0) for item in self])
    
    def shipping_cost(self):
        cost = decimal.Decimal(0)
        for ctype in self.ctype_list():
            cost += (ctype.model_class().get_shipping_cost([item for item in self if item.ctype() == ctype], self.shipping_options) or 0)
        return cost
    
    def get_available_shipping_options(self):
        options = ()
        for ctype in self.ctype_list():
            options += ctype.model_class().get_available_shipping_options([item for item in self if item.ctype() == ctype]) or ()
        return options
        
    def subtotal(self):
        return sum([(item.row_total() or 0) for item in self])
        
    def total(self):
        return decimal.Decimal(self.subtotal()) + self.shipping_cost()
        
    def errors(self):
        errors = []
        if not self.quantity():
            errors.append("No items in your cart.")
        
        for ctype in self.ctype_list():
            try:
                ctype.model_class().verify_purchase([item for item in self if item.ctype() == ctype])
            except CartIntegrityError, e:
                errors.append(e)
        #print errors
        return errors
    
    def is_valid(self):
        return len(self.errors()) == 0
    
  
    
  