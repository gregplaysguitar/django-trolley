# -*- coding: utf-8 -*-


from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

from models import Product, Category



def index(request, category_slug=None):
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category)
    else:
        category = None
        products = Product.objects.all()
    
        
    return render_to_response(
        'shop/index.html',
        {
            'products': products,
            'category': category,
        },
        RequestContext(request)
    )



def product(request, category_slug, product_slug):
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
        
    return render_to_response(
        'shop/product.html',
        {
            'product': product,
        },
        RequestContext(request)
    )


