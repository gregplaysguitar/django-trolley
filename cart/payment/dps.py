# -*- coding: utf-8 -*-

from django.conf import settings
import urllib, urllib2
from xml.etree import cElementTree as ElementTree
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404


PXPAY_URL = getattr(settings, 'PXPAY_URL', 'https://sec.paymentexpress.com/pxpay/pxaccess.aspx')
PXPAY_USERID = getattr(settings, 'PXPAY_USERID')
PXPAY_KEY = getattr(settings, 'PXPAY_KEY')


class PaymentBackend:
    """Payment backend which redirects to a DPS-hosted credit card page for payment."""
    
    def pxrequest(self, values):
        """Performs a generic request to pxpay."""
        req = urllib2.Request(PXPAY_URL, ElementTree.tostring(ConvertDictToXml(values)))
        response = urllib2.urlopen(req)
        
        string =  response.read()
        
        return ElementTree.fromstring(string)
    
    
    def read_result(self, result):
        """Retrieves pxpay response data, given a result hash."""
        values = {
            'ProcessResponse': {
                'PxPayUserId': PXPAY_USERID,
                'PxPayKey': PXPAY_KEY,
                'Response': result,
            }
        }
        return self.pxrequest(values)
    
    
    def payment_request(self, amount, merchant_ref, email, txn_id, return_url, txn_data=[]):
        """Makes a payment request to the pxpay server."""
        
        values = {
            'PxPayUserId': PXPAY_USERID,
            'PxPayKey': PXPAY_KEY,
            'TxnType': 'Purchase',
            'CurrencyInput' : 'NZD',

            'AmountInput': amount,
            'MerchantReference': merchant_ref,
            'EmailAddress': email,                
            'TxnId': txn_id,
            'UrlSuccess': return_url,
            'UrlFail': return_url,
        }
        count = 1
        for val in txn_data[:3]:
            values['TxnData%s' % count] = val
            count += 1
        
        return self.pxrequest({
            'GenerateRequest': values,
        })

    
    
    def paymentView(self, request, param, order):
        """View which handles the payment requests and redirects to the appropriate DPS page."""
        
        if param:
 
            payment_attempt = get_object_or_404(order.paymentattempt_set, hash=param)
                
            xml = self.read_result(request.GET.get('result'))
            
            result = []
            success = (xml.find('Success').text == '1')
            
            for el in xml:
                result.append("%s: %s" % (el.tag, el.text))
            payment_attempt.result = '\n'.join(result)
            payment_attempt.transaction_ref = xml.find('DpsTxnRef').text or ''
            payment_attempt.success = success
            payment_attempt.amount = xml.find('AmountSettlement').text or 0
            payment_attempt.save()
                
            order.payment_successful = success
            order.save()
            
            if success:
                return HttpResponseRedirect(order.get_absolute_url())
    
        payment_attempt = order.paymentattempt_set.create()
        
        return_url = 'http://%s%s' % (request.META['HTTP_HOST'], reverse('cart.views.payment', args=(order.hash, payment_attempt.hash,)))
        
        amount = "%.2f" % order.total()
        
        xml = self.payment_request(
            amount=amount,
            merchant_ref='Transaction #%s' % order.pk,
            email=order.email,
            txn_id=payment_attempt.hash,
            return_url=return_url,
            txn_data=[
                order.street_address.encode('ascii', 'replace'),
                order.suburb.encode('ascii', 'replace'),
                order.city.encode('ascii', 'replace'),
            ],
        )    
        
        return HttpResponseRedirect(xml.find('URI').text)
        




class XmlDictObject(dict):
    """
    Adds object like functionality to the standard dictionary.
    """

    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)
    
    def __getattr__(self, item):
        return self.__getitem__(item)
    
    def __setattr__(self, item, value):
        self.__setitem__(item, value)
    
    def __str__(self):
        if self.has_key('_text'):
            return self.__getitem__('_text')
        else:
            return ''

    @staticmethod
    def Wrap(x):
        """
        Static method to wrap a dictionary recursively as an XmlDictObject
        """

        if isinstance(x, dict):
            return XmlDictObject((k, XmlDictObject.Wrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject.Wrap(v) for v in x]
        else:
            return x

    @staticmethod
    def _UnWrap(x):
        if isinstance(x, dict):
            return dict((k, XmlDictObject._UnWrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject._UnWrap(v) for v in x]
        else:
            return x
        
    def UnWrap(self):
        """
        Recursively converts an XmlDictObject to a standard dictionary and returns the result.
        """

        return XmlDictObject._UnWrap(self)

def _ConvertDictToXmlRecurse(parent, dictitem):
    assert type(dictitem) is not type([])

    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.iteritems():
            if str(tag) == '_text':
                parent.text = str(child)
            elif type(child) is type([]):
                # iterate through the array and convert
                for listchild in child:
                    elem = ElementTree.Element(tag)
                    parent.append(elem)
                    _ConvertDictToXmlRecurse(elem, listchild)
            else:                
                elem = ElementTree.Element(tag)
                parent.append(elem)
                _ConvertDictToXmlRecurse(elem, child)
    else:
        parent.text = str(dictitem)
    
def ConvertDictToXml(xmldict):
    """
    Converts a dictionary to an XML ElementTree Element 
    """

    roottag = xmldict.keys()[0]
    root = ElementTree.Element(roottag)
    _ConvertDictToXmlRecurse(root, xmldict[roottag])
    return root

def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()
    
    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))
    
    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        if nodedict.has_key(child.tag):
            # found duplicate tag, force a list
            if type(nodedict[child.tag]) is type([]):
                # append to existing list
                nodedict[child.tag].append(newitem)
            else:
                # convert to list
                nodedict[child.tag] = [nodedict[child.tag], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[child.tag] = newitem

    if node.text is None: 
        text = ''
    else: 
        text = node.text.strip()
    
    if len(nodedict) > 0:            
        # if we have a dictionary add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        nodedict = text
        
    return nodedict
        
def ConvertXmlToDict(root, dictclass=XmlDictObject):
    """
    Converts an XML file or ElementTree Element to a dictionary
    """

    # If a string is passed in, try to open it as a file
    if type(root) == type(''):
        root = ElementTree.parse(root).getroot()
    elif not isinstance(root, ElementTree.Element):
        raise TypeError, 'Expected ElementTree.Element or file path string'

    return dictclass({root.tag: _ConvertXmlToDictRecurse(root, dictclass)})

