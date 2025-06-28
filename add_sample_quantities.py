#!/usr/bin/env python
"""
Script to add sample quantities to existing products
Run this script to populate the quantity field for existing products
"""

import os
import sys
import django
import requests

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

def send_telegram_message(order_details):
    bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
    chat_id = '<YOUR_CHAT_ID>'  # Replace with your Telegram user or group chat ID
    message = f"New order: {order_details}"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    requests.post(url, data=data)

if __name__ == '__main__':
    add_sample_quantities() 