#!/usr/bin/env python3
"""
Utility script to get Telegram chat ID for bot integration
"""

import requests
import json

def get_chat_id():
    """
    Get your chat ID by sending a message to your bot first,
    then running this script to get the chat ID from the bot's updates
    """
    bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
    
    # Get updates from bot
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            if data['ok'] and data['result']:
                print("Recent messages to your bot:")
                for update in data['result']:
                    if 'message' in update:
                        message = update['message']
                        chat = message['chat']
                        print(f"Chat ID: {chat['id']}")
                        print(f"Chat Type: {chat['type']}")
                        print(f"From: {chat.get('first_name', '')} {chat.get('last_name', '')}")
                        print(f"Username: @{chat.get('username', 'N/A')}")
                        print("-" * 50)
            else:
                print("No recent messages found.")
                print("To get your chat ID:")
                print("1. Open Telegram")
                print("2. Search for @Getme_Phone_Shop_bot")
                print("3. Start a conversation with your bot")
                print("4. Send any message to the bot")
                print("5. Run this script again")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def send_test_message(chat_id):
    """
    Send a test message to verify the chat ID is correct
    """
    bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🔔 Test message from your e-commerce site! Your Telegram integration is working! 🎉',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
        else:
            print(f"❌ Error sending test message: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Telegram Bot Chat ID Utility")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Get chat ID from recent messages")
        print("2. Send test message (requires chat ID)")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            get_chat_id()
        elif choice == "2":
            chat_id = input("Enter chat ID: ").strip()
            if chat_id:
                send_test_message(chat_id)
            else:
                print("Please enter a valid chat ID")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.") 