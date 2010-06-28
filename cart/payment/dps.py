from django.conf import settings
import urllib, urllib2
from xml.etree import cElementTree as ElementTree
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404


class PaymentBackend:
    
    def paymentView(self, request, param, order):
        
        if param:
 
            payment_attempt = get_object_or_404(order.paymentattempt_set, hash=param)
                
            values = {
                'ProcessResponse': {
                    'PxPayUserId': settings.PXPAY_USERID,
                    'PxPayKey': settings.PXPAY_KEY,
                    'Response': request.GET.get('result'),
                }
            }
            req = urllib2.Request(settings.PXPAY_URL, ElementTree.tostring(ConvertDictToXml(values)))
            response = urllib2.urlopen(req)
            
            string =  response.read()
            
            result = []
            xml = ElementTree.fromstring(string)
            for el in xml:
                result.append("%s: %s" % (el.tag, el.text))
            payment_attempt.result = '\n'.join(result)
            payment_attempt.save()
                
            order.payment_successful = (xml.find('Success').text == '1')
            order.transaction_ref = xml.find('DpsTxnRef').text
            order.save()
            
            
                
            return HttpResponseRedirect(order.get_absolute_url())
        else:
            
            payment_attempt = order.paymentattempt_set.create()
           
            host = 'http://' + request.META['HTTP_HOST']
            
            amount = "%.2f" % order.total()
            values = {
                'GenerateRequest': {
                    'PxPayUserId': settings.PXPAY_USERID,
                    'PxPayKey': settings.PXPAY_KEY,
                    'AmountInput': amount,
                    'CurrencyInput' : 'NZD',
                    'MerchantReference': 'Transaction #%s' % order.pk,
                    'EmailAddress': order.email,
                    'TxnData1': order.street_address,
                    'TxnData2': order.suburb,
                    'TxnData3': order.city,
                    'TxnType': 'Purchase',
                    'TxnId': payment_attempt.hash,
                    'UrlSuccess': host + reverse('cart.views.payment', args=(payment_attempt.hash,)),
                    'UrlFail': host + reverse('cart.views.payment', args=(payment_attempt.hash,)),
                    #'Opt': None,
                    #'BillingId': 0,
                    #'EnableAddBillCard': 0,
                }
            }
            #print values, ElementTree.tostring(ConvertDictToXml(values))
            
            
            req = urllib2.Request(settings.PXPAY_URL, ElementTree.tostring(ConvertDictToXml(values)))
            response = urllib2.urlopen(req)
            
            string =  response.read()
            #print string
            
            xml = ElementTree.fromstring(string)
            
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

