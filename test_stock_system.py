#!/usr/bin/env python
"""
Test script to verify the stock management system
Run this script to test stock functionality
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
from cart.cart import Cart
from django.test import RequestFactory
from django.contrib.auth.models import User

def test_stock_system():
    """Test the stock management system"""
    print("🧪 Testing Stock Management System")
    print("=" * 50)
    
    # Get a test product
    try:
        product = Product.objects.first()
        if not product:
            print("❌ No products found in database")
            return
        
        print(f"📦 Testing with product: {product.name}")
        print(f"   Current stock: {product.quantity}")
        print(f"   Stock status: {product.stock_status}")
        print(f"   Is in stock: {product.is_in_stock}")
        
        # Test stock methods
        print("\n🔍 Testing stock methods:")
        
        # Test has_sufficient_stock
        test_quantity = 5
        has_stock = product.has_sufficient_stock(test_quantity)
        print(f"   Has sufficient stock for {test_quantity}: {has_stock}")
        
        # Test reduce_stock
        if product.quantity > 0:
            original_quantity = product.quantity
            reduce_amount = min(2, original_quantity)
            success = product.reduce_stock(reduce_amount)
            print(f"   Reduce stock by {reduce_amount}: {success}")
            print(f"   New quantity: {product.quantity}")
            
            # Restore stock
            product.add_stock(reduce_amount)
            print(f"   Restored stock: {product.quantity}")
        
        # Test cart stock validation
        print("\n🛒 Testing cart stock validation:")
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {}
        
        cart = Cart(request)
        
        # Test adding to cart
        if product.is_in_stock:
            success, message = cart.add(product, 1)
            print(f"   Add to cart: {success} - {message}")
            
            # Test adding more than available
            if product.quantity > 0:
                over_quantity = product.quantity + 5
                success, message = cart.add(product, over_quantity)
                print(f"   Add over stock limit: {success} - {message}")
        else:
            print("   Product is out of stock, skipping cart tests")
        
        print("\n✅ Stock management system test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def show_stock_summary():
    """Show a summary of all product stock levels"""
    print("\n📊 Stock Summary")
    print("=" * 50)
    
    products = Product.objects.all()
    
    out_of_stock = 0
    low_stock = 0
    in_stock = 0
    
    for product in products:
        if product.quantity == 0:
            out_of_stock += 1
        elif product.quantity <= 5:
            low_stock += 1
        else:
            in_stock += 1
    
    print(f"📦 Total products: {products.count()}")
    print(f"🔴 Out of stock: {out_of_stock}")
    print(f"🟡 Low stock (≤5): {low_stock}")
    print(f"🟢 In stock (>5): {in_stock}")
    
    print("\n📋 Low stock products:")
    low_stock_products = Product.objects.filter(quantity__lte=5, quantity__gt=0)
    for product in low_stock_products:
        print(f"   • {product.name}: {product.quantity} units")
    
    print("\n🚫 Out of stock products:")
    out_of_stock_products = Product.objects.filter(quantity=0)
    for product in out_of_stock_products:
        print(f"   • {product.name}: {product.quantity} units")

if __name__ == '__main__':
    test_stock_system()
    show_stock_summary() 