#!/usr/bin/env python
"""
Script to add sample quantities to existing products
Run this script to populate the quantity field for existing products
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product
import random

def add_sample_quantities():
    """Add random quantities to all products"""
    products = Product.objects.all()
    
    for product in products:
        # Generate a random quantity between 0 and 50
        quantity = random.randint(0, 50)
        product.quantity = quantity
        product.save()
        
        print(f"Updated {product.name}: {quantity} units in stock")
    
    print(f"\nUpdated quantities for {products.count()} products")

if __name__ == '__main__':
    add_sample_quantities() 