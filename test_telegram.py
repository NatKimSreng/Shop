#!/usr/bin/env python3
"""
Test script to verify Telegram notification function
"""

import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_notification(order_id, total_amount, customer_name, customer_email, customer_phone, delivery_name, payment_method, items_list, city, country):
    """
    Send order notification to Telegram group
    """
    try:
        bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
        chat_id = '-4862435107'  # Bot Get me Shop group
        
        # Calculate total items
        total_items = sum(item['quantity'] for item in items_list)
        
        # Format a concise message for group
        message = f"🛒 *NEW ORDER #{order_id}*\n\n"
        message += f"💰 *Total:* ${total_amount:.2f}\n"
        message += f"📦 *Items:* {total_items} item{'s' if total_items != 1 else ''}\n"
        message += f"👤 *Customer:* {customer_name}\n"
        message += f"📧 *Email:* {customer_email}\n"
        message += f"📱 *Phone:* {customer_phone}\n"
        message += f"🚚 *Delivery:* {delivery_name}\n"
        message += f"💳 *Payment:* {payment_method}\n\n"
        
        # List items briefly
        message += f"📋 *Order Items:*\n"
        for item in items_list:
            message += f"• {item['name']} x{item['quantity']}\n"
        
        message += f"\n📍 *Address:* {city}, {country}"
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram notification sent successfully for order {order_id}")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Telegram Notification Function")
    print("=" * 40)
    
    # Test data
    test_order = {
        'order_id': 999,
        'total_amount': 299.99,
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '+1234567890',
        'delivery_name': 'Express Delivery',
        'payment_method': 'Credit Card',
        'items_list': [
            {'name': 'iPhone 15 Pro', 'quantity': 1},
            {'name': 'AirPods Pro', 'quantity': 1}
        ],
        'city': 'New York',
        'country': 'United States'
    }
    
    print("Sending test notification...")
    success = send_telegram_notification(**test_order)
    
    if success:
        print("✅ Test notification sent successfully!")
        print("Check your 'Bot Get me Shop' group to see the message.")
    else:
        print("❌ Test notification failed!")
        print("Check the error messages above.") 