"""

from cart import Cart

class CartMiddleware(object):
    def process_request(self, request):
        if not ('cart' in request):
            request.cart = Cart(request)
            
            """