# -*- coding: utf-8 -*-


from django.contrib import admin

from models import Category, Product


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )

admin.site.register(Category, CategoryAdmin)

   
   
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category',)
    list_filter = ('category', )
    search_fields = ('name', 'description', )
        
admin.site.register(Product, ProductAdmin)
