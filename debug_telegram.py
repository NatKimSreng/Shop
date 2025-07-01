#!/usr/bin/env python3
"""
Comprehensive Telegram Bot Debugging Script
Use this script to diagnose and fix Telegram bot issues in Proxmox environments
"""

import os
import sys
import requests
import json
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramBotDebugger:
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '-4862435107')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def test_bot_connection(self):
        """Test basic bot connectivity"""
        print("🔍 Testing Bot Connection...")
        print("=" * 40)
        
        try:
            # Test bot info
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Bot connected successfully!")
                    print(f"   Bot Name: {bot_info['result']['first_name']}")
                    print(f"   Username: @{bot_info['result']['username']}")
                    print(f"   Bot ID: {bot_info['result']['id']}")
                    return True
                else:
                    print(f"❌ Bot API error: {bot_info.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Connection timeout - check network connectivity")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_chat_access(self):
        """Test if bot can access the chat"""
        print("\n💬 Testing Chat Access...")
        print("=" * 40)
        
        try:
            # Test chat info
            response = requests.get(f"{self.base_url}/getChat", 
                                  params={'chat_id': self.chat_id}, 
                                  timeout=10)
            
            if response.status_code == 200:
                chat_info = response.json()
                if chat_info.get('ok'):
                    chat = chat_info['result']
                    print(f"✅ Chat access successful!")
                    print(f"   Chat Type: {chat['type']}")
                    print(f"   Chat ID: {chat['id']}")
                    if chat['type'] in ['group', 'supergroup']:
                        print(f"   Group Name: {chat.get('title', 'N/A')}")
                    return True
                else:
                    print(f"❌ Chat access error: {chat_info.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat access error: {e}")
            return False
    
    def test_message_sending(self):
        """Test sending a message"""
        print("\n📤 Testing Message Sending...")
        print("=" * 40)
        
        test_message = f"🧪 Test message from Proxmox environment\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔧 Debug session active"
        
        try:
            response = requests.post(f"{self.base_url}/sendMessage", 
                                   data={
                                       'chat_id': self.chat_id,
                                       'text': test_message,
                                       'parse_mode': 'Markdown'
                                   }, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Test message sent successfully!")
                    print(f"   Message ID: {result['result']['message_id']}")
                    return True
                else:
                    print(f"❌ Message sending error: {result.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Message sending timeout")
            return False
        except Exception as e:
            print(f"❌ Message sending error: {e}")
            return False
    
    def check_network_connectivity(self):
        """Check network connectivity to Telegram API"""
        print("\n🌐 Testing Network Connectivity...")
        print("=" * 40)
        
        # Test DNS resolution
        try:
            import socket
            socket.gethostbyname('api.telegram.org')
            print("✅ DNS resolution successful")
        except Exception as e:
            print(f"❌ DNS resolution failed: {e}")
            return False
        
        # Test HTTP connectivity
        try:
            response = requests.get('https://api.telegram.org', timeout=10)
            print(f"✅ HTTP connectivity successful (Status: {response.status_code})")
            return True
        except Exception as e:
            print(f"❌ HTTP connectivity failed: {e}")
            return False
    
    def check_environment_variables(self):
        """Check environment variable configuration"""
        print("\n⚙️ Checking Environment Variables...")
        print("=" * 40)
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        print(f"Bot Token: {'✅ Set' if bot_token else '❌ Not set'}")
        print(f"Chat ID: {'✅ Set' if chat_id else '❌ Not set'}")
        
        if bot_token and chat_id:
            print("✅ All required environment variables are set")
            return True
        else:
            print("❌ Missing required environment variables")
            print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return False
    
    def get_recent_updates(self):
        """Get recent bot updates for debugging"""
        print("\n📋 Getting Recent Updates...")
        print("=" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/getUpdates", timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates.get('ok'):
                    recent_updates = updates['result']
                    print(f"Found {len(recent_updates)} recent updates")
                    
                    for i, update in enumerate(recent_updates[-5:], 1):  # Show last 5
                        if 'message' in update:
                            msg = update['message']
                            chat = msg['chat']
                            print(f"  {i}. Chat ID: {chat['id']}, Type: {chat['type']}")
                            if chat['type'] in ['group', 'supergroup']:
                                print(f"     Group: {chat.get('title', 'N/A')}")
                    return True
                else:
                    print(f"❌ Error getting updates: {updates.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting updates: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Telegram Bot Debug")
        print("=" * 50)
        print(f"Bot Token: {self.bot_token[:20]}...")
        print(f"Chat ID: {self.chat_id}")
        print("=" * 50)
        
        tests = [
            ("Environment Variables", self.check_environment_variables),
            ("Network Connectivity", self.check_network_connectivity),
            ("Bot Connection", self.test_bot_connection),
            ("Chat Access", self.test_chat_access),
            ("Recent Updates", self.get_recent_updates),
            ("Message Sending", self.test_message_sending),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All tests passed! Telegram bot should work correctly.")
        else:
            print("⚠️ Some tests failed. Check the issues above.")
        
        return passed == len(results)

def main():
    debugger = TelegramBotDebugger()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'connection':
            debugger.test_bot_connection()
        elif command == 'chat':
            debugger.test_chat_access()
        elif command == 'message':
            debugger.test_message_sending()
        elif command == 'network':
            debugger.check_network_connectivity()
        elif command == 'env':
            debugger.check_environment_variables()
        elif command == 'updates':
            debugger.get_recent_updates()
        else:
            print("Unknown command. Use: connection, chat, message, network, env, updates, or all")
    else:
        # Run comprehensive test
        debugger.run_comprehensive_test()

if __name__ == "__main__":
    main() 