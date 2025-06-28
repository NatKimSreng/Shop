# Telegram Bot Integration for E-commerce Site

This integration connects your e-commerce checkout process with your Telegram bot `@Getme_Phone_Shop_bot` to provide real-time order notifications to your team group.

## Features

1. **Group Notifications**: Receive order notifications in your Telegram group when customers complete checkout
2. **Concise Alerts**: Brief, informative messages suitable for group communication
3. **Team Collaboration**: All team members in the group can see new orders instantly

## Current Setup

- **Bot Username**: @Getme_Phone_Shop_bot
- **Group**: "Bot Get me Shop" 
- **Group Chat ID**: -4862435107
- **Status**: ✅ Connected and working

## How It Works

### Group Notifications
When a customer completes checkout, your bot sends a concise message to your group containing:
- 🛒 Order ID and total amount
- 📦 Number of items ordered
- 👤 Customer name, email, and phone
- 🚚 Delivery method and payment type
- 📋 List of ordered items
- 📍 Customer location

### Message Format Example

```
🛒 NEW ORDER #123

💰 Total: $299.99
📦 Items: 2 items
👤 Customer: John Doe
📧 Email: john@example.com
📱 Phone: +1234567890
🚚 Delivery: Express
💳 Payment: Credit Card

📋 Order Items:
• iPhone 15 Pro x1
• AirPods Pro x1

📍 Address: New York, United States
```

## Setup Instructions

### Step 1: Add Bot to Your Group

1. **Open Telegram** and go to your group "Bot Get me Shop"
2. **Add your bot** @Getme_Phone_Shop_bot to the group
3. **Make the bot an admin** (optional but recommended for better functionality)
4. **Send a message** in the group to activate the bot

### Step 2: Get Group Chat ID

Run the utility script to get your group's chat ID:

```bash
python get_group_chat_id.py
```

### Step 3: Update Chat ID (if needed)

If you want to use a different group, update the chat ID in `payment/views.py`:

```python
chat_id = '-4862435107'  # Replace with your group chat ID
```

## Files Modified

- `payment/views.py` - Added Telegram group notification function
- `payment/templates/payment/payment_success.html` - Added Telegram bot button
- `requirements.txt` - Added requests library
- `get_group_chat_id.py` - Utility script for group setup
- `TELEGRAM_INTEGRATION_README.md` - This documentation

## Troubleshooting

### Bot Not Sending Messages to Group
1. **Check bot permissions**: Make sure the bot is added to the group
2. **Verify chat ID**: Ensure you're using the correct group chat ID (starts with `-`)
3. **Test the bot**: Use the utility script to send a test message

### Group Chat ID Types
- **Group**: Negative number starting with `-` (e.g., `-4862435107`)
- **Supergroup**: Negative number starting with `-100` (e.g., `-1001234567890`)

## Security Notes

- **Group privacy**: Only add trusted team members to the group
- **Bot permissions**: Limit bot permissions to only what's necessary
- **Token security**: Keep your bot token secure and don't share it publicly

## Customization

### Modify Message Format
Edit the `send_telegram_notification` function in `payment/views.py` to customize:
- Message content and format
- Information included/excluded
- Emoji usage

### Add More Features
- **Order status updates**: Send notifications when order status changes
- **Delivery tracking**: Send delivery updates to the group
- **Inventory alerts**: Notify when stock is low
- **Sales reports**: Daily/weekly sales summaries

## Support

If you need help with the Telegram group integration:
1. Check the troubleshooting section above
2. Use the `get_group_chat_id.py` script for testing
3. Check Django logs for error messages
4. Verify bot permissions in your Telegram group 