# -*- coding: utf-8 -*-

import pickle
import types
import hashlib
import decimal

from django.contrib.contenttypes.models import ContentType
from UserDict import DictMixin



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
    
    def update_quantity(self, q):
        self['quantity'] = q
        self._original_row_total = None
        self._row_total = None
    
    def original_row_total(self):
        if not self._original_row_total:
            self._original_row_total = decimal.Decimal(self.product.get_price(self.get('quantity', 0), self['options']))
        return self._original_row_total
    _original_row_total = None
    
    def row_total(self):
        if not self._row_total:
            if hasattr(self.product, 'get_discounted_price'):
                self._row_total = decimal.Decimal(self.product.get_discounted_price(self.get('quantity', 0), self['options'], self.cart))
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
    
    @property
    def formindex(self):
        return hashlib.md5(unicode(self.createindex())).hexdigest()

    def options_text(self):
        return ", ".join([self['options'][key] for key in self['options']])
  
    
class BaseCart:
    '''Abstract Cart class - don't use this directly. Should be extended by custom Cart
       classes.'''
       
    def __init__(self, request):
        if not request.session.get(CART_INDEX, None):
            request.session[CART_INDEX] = {}
        
        for index in ('lines', 'data', 'detail_data', 'shipping_options'):
            if index not in request.session[CART_INDEX]:
                request.session[CART_INDEX][index] = {}
            setattr(self, index, request.session[CART_INDEX][index])
       
        self.session = request.session
    
    def __iter__(self):
        keys = self.lines.keys()
        keys.sort()
        
        for item in map(self.lines.get, keys):
            try:
                yield item
            except ItemIntegrityError:
                pass

    
    def as_dict(self):
        data = {
            'quantity': self.quantity(),
            'subtotal': str(self.subtotal()),
            'total': str(self.total()),
            'shipping_cost': str(self.shipping_cost()),
            'lines': [],
        }
        for item in self:
            line = dict(item)
            line['product'] = str(item.product)
            line['original_row_total'] = str(item.original_row_total())
            line['row_total'] = str(item.row_total())
            line['index'] = item.formindex
            data['lines'].append(line)
        return data
    
    def ctype_list(self):
        list = []
        for item in self:
            ctype = item.ctype()
            if not ctype in list:
                list.append(ctype)
        return list
    
    def add(self, product, quantity=1, options={}):
        index = create_cart_index(product, options)
        if not self.lines.get(index, False):
            self.lines[index] = Item({
                'product_pk': product.pk,
                'product_content_type_id': ContentType.objects.get_for_model(product).pk,
                'options': options,
                'quantity': quantity
            }, self)
        else:
            self.lines[index].update_quantity(self.lines[index]['quantity'] + quantity)
        
        self.modified()
            
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
                self.lines[create_cart_index(product, options)].update_quantity(q) 
            else:
                self.remove(product, options)
            self.modified()
        except IndexError:
            raise ItemDoesNotExist
    
    def modified(self):
        self.session.modified = True
    
    def get(self, product, options={}):
        return Item(self.lines[create_cart_index(product, options)], self)
    
    def clear(self):
        for index in self.lines.keys():
            del(self.lines[index])
        for index in self.data.keys():
            del(self.data[index])
        self.modified()
        
    def quantity(self):
        return sum([item.get('quantity', 0) for item in self])
        
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
                self.verify_purchase()
            except CartIntegrityError, e:
                errors.append(e)
        #print errors
        return errors
    
    def is_valid(self):
        return len(self.errors()) == 0
    
    def shipping_cost(self):
        '''Should return total shipping cost for the cart.'''
        raise NotImplementedError()
    
    def verify_purchase(self):
        '''Should raise a CartIntegrityError if the purchase is not allowed.'''
        raise NotImplementedError()
    
    def get_available_shipping_options(self):
        '''Should return a list of shipping options for the cart, each of the form
               
               (key, name, choices)
               
           where "choices" is a list of key,value pairs in the usual django format.'''
        raise NotImplementedError()


def has_static_method(obj, attr):
    return isinstance(getattr(obj, attr, None), types.FunctionType)

class Cart(BaseCart):
    '''Default Cart class, providing simple defaults for all customisable methods.'''
    
    def shipping_cost(self):
        if any([has_static_method(c, 'shipping_cost') for c in self.ctype_list()]):
            raise DeprecationWarning(u'The shipping_cost static method is deprecated; use a HELPER_MODULE instead.')
        return 0
    
    def verify_purchase(self):
        if any([has_static_method(c, 'verify_purchase') for c in self.ctype_list()]):
            raise DeprecationWarning(u'The verify_purchase static method is deprecated; use a HELPER_MODULE instead.')
        return
    
    def get_available_shipping_options(self):
        if any([has_static_method(c, 'get_available_shipping_options') for c in self.ctype_list()]):
            raise DeprecationWarning(u'The get_available_shipping_options static method is deprecated; use a HELPER_MODULE instead.')
        return []
    
