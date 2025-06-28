#!/usr/bin/env python3
"""
Script to get Telegram group chat ID for order notifications
"""

import requests

def get_group_chat_id():
    """
    Instructions to get your group chat ID
    """
    print("📋 How to get your Telegram Group Chat ID:")
    print("=" * 50)
    print()
    print("1. Create a group in Telegram (if you haven't already)")
    print("2. Add your bot @Getme_Phone_Shop_bot to the group")
    print("3. Make the bot an admin of the group (optional but recommended)")
    print("4. Send any message in the group")
    print("5. Run this script to get the group chat ID")
    print()
    
    bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            if data['ok'] and data['result']:
                print("📱 Recent messages to your bot:")
                print("-" * 30)
                
                group_found = False
                for update in data['result']:
                    if 'message' in update:
                        message = update['message']
                        chat = message['chat']
                        
                        if chat['type'] == 'group' or chat['type'] == 'supergroup':
                            group_found = True
                            print(f"🏷️  Group Name: {chat.get('title', 'N/A')}")
                            print(f"🆔 Group Chat ID: {chat['id']}")
                            print(f"📝 Chat Type: {chat['type']}")
                            print(f"👤 From: {message.get('from', {}).get('first_name', 'N/A')}")
                            print("-" * 30)
                
                if not group_found:
                    print("❌ No group messages found.")
                    print()
                    print("To add your bot to a group:")
                    print("1. Open Telegram")
                    print("2. Go to your group")
                    print("3. Click on group name → Add members")
                    print("4. Search for @Getme_Phone_Shop_bot")
                    print("5. Add the bot to the group")
                    print("6. Send a message in the group")
                    print("7. Run this script again")
            else:
                print("❌ No recent messages found.")
                print("Make sure your bot is added to the group and someone sent a message.")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_group_message(chat_id):
    """
    Send a test message to the group
    """
    bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🔔 Test message from your e-commerce site! Order notifications will be sent to this group. 🎉',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Test message sent successfully to the group!")
        else:
            print(f"❌ Error sending test message: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏪 Telegram Group Chat ID for Order Notifications")
    print("=" * 55)
    
    while True:
        print("\nOptions:")
        print("1. Get group chat ID from recent messages")
        print("2. Send test message to group (requires chat ID)")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            get_group_chat_id()
        elif choice == "2":
            chat_id = input("Enter group chat ID: ").strip()
            if chat_id:
                test_group_message(chat_id)
            else:
                print("Please enter a valid group chat ID")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.") 