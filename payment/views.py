# payment/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
import logging
import qrcode
from io import BytesIO
import base64
from django.shortcuts import render, redirect
from django.contrib import messages
import logging
import requests
from cart.cart import Cart
from store.models import Product
from .forms import ShippingForm, PaymentForm
from .models import ShippingAddress, Order, OrderItem, DeliveryOption
logger = logging.getLogger(__name__)

@login_required(login_url='/register/')

def checkout(request):
    cart = Cart(request)
    delivery_options = DeliveryOption.objects.filter(is_active=True)
    logger.debug(f"Delivery options fetched: {list(delivery_options.values('id', 'name', 'price'))}")

    # Ensure at least one delivery option exists
    if not delivery_options.exists():
        logger.error("No active delivery options found in database")
        default_option, _ = DeliveryOption.objects.get_or_create(
            name="Standard",
            defaults={'price': 5.00, 'estimated_days': 5, 'description': 'Standard delivery', 'is_active': True}
        )
        delivery_options = DeliveryOption.objects.filter(is_active=True)
        

    # Calculate cart total without delivery
    try:
        cart_total_raw = cart.get_total_price() or 0
        logger.debug(f"Raw cart total: {cart_total_raw}")
        if isinstance(cart_total_raw, str):
            cleaned_total = ''.join(char for char in cart_total_raw if char.isdigit() or char in ['.', '-'])
            if cleaned_total.count('.') > 1:
                logger.error(f"Invalid cart total format: multiple decimal points in '{cleaned_total}'")
                raise ValueError("Invalid cart total format: multiple decimal points")
            if not cleaned_total.replace('.', '').replace('-', '').isdigit():
                logger.error(f"Invalid cart total format: non-numeric characters in '{cleaned_total}'")
                raise ValueError("Invalid cart total format: non-numeric characters")
            if cleaned_total in ['', '.', '-']:
                logger.error(f"Invalid cart total format: empty or incomplete number '{cleaned_total}'")
                raise ValueError("Invalid cart total format: empty or incomplete number")
            cart_total = float(cleaned_total)
        else:
            cart_total = float(cart_total_raw)
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting cart total: {str(e)}")
        return render(request, "payment/checkout.html", {
            'order': {'get_cart_items': 0, 'get_cart_total': 0, 'delivery_cost': 0, 'grand_total': 0},
            'items': [],
            'delivery_options': delivery_options,
            'selected_delivery_id': None,
            'shipping_form': ShippingForm(),
            'payment_form': PaymentForm(),
            'error': "Invalid cart total. Please check your cart and try again."
        })

    # Default delivery option
    default_delivery = delivery_options.first()
    selected_delivery_id = request.POST.get('delivery_option', default_delivery.id)
    logger.debug(f"Selected delivery ID: {selected_delivery_id}")

    # Get selected delivery option
    selected_delivery = DeliveryOption.objects.filter(id=selected_delivery_id, is_active=True).first() or default_delivery
    delivery_cost = float(selected_delivery.price) if selected_delivery else 0
    
    order = {
        'get_cart_items': cart.__len__(),
        'get_cart_total': cart_total,
        'delivery_cost': delivery_cost,
        'grand_total': cart_total + delivery_cost
    }
    
    product_ids = [int(pid) for pid in cart.cart.keys()]
    products = Product.objects.filter(id__in=product_ids, Is_sale=True)
    product_dict = {str(product.id): product for product in products}

    logger.debug(f"product_ids: {product_ids}")
    logger.debug(f"product_dict keys: {list(product_dict.keys())}")

    if not product_ids or any(str(pid) not in product_dict for pid in product_ids):
        logger.warning("Cart contains unavailable products or is empty")
        return render(request, "payment/checkout.html", {
            'order': order,
            'items': [],
            'delivery_options': delivery_options,
            'selected_delivery_id': selected_delivery_id,
            'error': "Your cart is empty or contains unavailable products."
        })

    items = []
    for pid in product_ids:
        product = product_dict.get(str(pid))
        if product:
            try:
                price_raw = cart.cart[str(pid)]['price']
                if isinstance(price_raw, str):
                    cleaned_price = ''.join(char for char in price_raw if char.isdigit() or char in ['.', '-'])
                    if cleaned_price.count('.') > 1:
                        logger.error(f"Invalid price format for product ID {pid}: multiple decimal points in '{cleaned_price}'")
                        raise ValueError(f"Invalid price format for product ID {pid}: multiple decimal points")
                    if not cleaned_price.replace('.', '').replace('-', '').isdigit():
                        logger.error(f"Invalid price format for product ID {pid}: non-numeric characters in '{cleaned_price}'")
                        raise ValueError(f"Invalid price format for product ID {pid}: non-numeric characters")
                    if cleaned_price in ['', '.', '-']:
                        logger.error(f"Invalid price format for product ID {pid}: empty or incomplete number '{cleaned_price}'")
                        raise ValueError(f"Invalid price format for product ID {pid}: empty or incomplete number")
                    price = float(cleaned_price)
                else:
                    price = float(price_raw)
                items.append({
                    'product': {
                        'id': pid,
                        'name': product.name,
                        'price': price,
                        'imageURL': product.imageURL
                    },
                    'quantity': cart.cart[str(pid)]['quantity'],
                    'get_total': price * cart.cart[str(pid)]['quantity']
                })
            except (AttributeError, ValueError) as e:
                logger.error(f"Error processing product ID {pid}: {e}")
                return render(request, "payment/checkout.html", {
                    'order': order,
                    'items': [],
                    'delivery_options': delivery_options,
                    'selected_delivery_id': selected_delivery_id,
                    'error': f"Invalid product data for ID {pid}."
                })
        else:
            logger.warning(f"Product ID {pid} not found in product_dict")
            return render(request, "payment/checkout.html", {
                'order': order,
                'items': [],
                'delivery_options': delivery_options,
                'selected_delivery_id': selected_delivery_id,
                'error': f"Product ID {pid} is no longer available."
            })

    shipping_form = ShippingForm(request.POST or None)
    payment_form = PaymentForm(request.POST or None)

    # Generate QR code for bank transfer if selected
    qr_code = None
    if request.POST.get('payment_method') == 'bank_transfer':
        try:
            payment_data = f"Bank: Example Bank\nAccount: 1234567890\nAmount: ${order['grand_total']:.2f}"
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(payment_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            qr_code = None

    if request.method == 'POST' and shipping_form.is_valid() and payment_form.is_valid():
        try:
            # Validate stock before processing order
            stock_errors = cart.validate_stock()
            if stock_errors:
                error_message = "Stock validation failed: " + "; ".join(stock_errors)
                messages.error(request, error_message)
                return render(request, "payment/checkout.html", {
                    'order': order,
                    'items': items,
                    'delivery_options': delivery_options,
                    'selected_delivery_id': selected_delivery_id,
                    'shipping_form': shipping_form,
                    'payment_form': payment_form,
                    'qr_code': qr_code
                })

            # Save shipping address
            shipping_address = shipping_form.save(commit=False)
            logger.debug(f"Saving shipping address for user: {request.user}")
            shipping_address.user = request.user
            shipping_address.save()

            # Create Order
            logger.debug(f"Creating order with amount_paid: {order['grand_total']}")
            new_order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                delivery_option=selected_delivery,
                payment_method=payment_form.cleaned_data['payment_method'],
                amount_paid=order['grand_total']
            )

            # Create OrderItems and reduce stock
            order_items = []
            for product_id, item in cart.cart.items():
                product = product_dict.get(product_id)
                if product:
                    price_raw = item['price']
                    logger.debug(f"Processing OrderItem for product ID {product_id}, price: {price_raw}")
                    if isinstance(price_raw, str):
                        cleaned_price = ''.join(char for char in price_raw if char.isdigit() or char in ['.', '-'])
                        if cleaned_price.count('.') > 1:
                            logger.error(f"Invalid price format for OrderItem product ID {product_id}: multiple decimal points in '{cleaned_price}'")
                            raise ValueError(f"Invalid price format for product ID {product_id}")
                        if not cleaned_price.replace('.', '').replace('-', '').isdigit():
                            logger.error(f"Invalid price format for OrderItem product ID {product_id}: non-numeric characters in '{cleaned_price}'")
                            raise ValueError(f"Invalid price format for product ID {product_id}")
                        if cleaned_price in ['', '.', '-']:
                            logger.error(f"Invalid price format for OrderItem product ID {product_id}: empty or incomplete number '{cleaned_price}'")
                            raise ValueError(f"Invalid price format for product ID {product_id}")
                        price = float(cleaned_price)
                    else:
                        price = float(price_raw)
                    
                    # Reduce stock
                    quantity = item['quantity']
                    if not product.reduce_stock(quantity):
                        logger.error(f"Insufficient stock for product ID {product_id}")
                        raise ValueError(f"Insufficient stock for {product.name}")
                    
                    order_item = OrderItem.objects.create(
                        order=new_order,
                        product=product,
                        quantity=quantity,
                        price=price
                    )
                    order_items.append(order_item)
                else:
                    logger.error(f"Product ID {product_id} not found during OrderItem creation")
                    raise ValueError(f"Product ID {product_id} not found")

            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            logger.debug("Cart cleared by resetting session['cart']")

            # Set session data for success page
            request.session['payment_successful'] = True
            request.session['order_id'] = new_order.id
            request.session['order_items'] = [
                {
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.get_total())
                } for item in order_items
            ]
            request.session['shipping_address'] = {
                'full_name': shipping_address.shipping_full_name,
                'email': shipping_address.shipping_email,
                'address1': shipping_address.shipping_address1,
                'address2': shipping_address.shipping_address2 or '',
                'city': shipping_address.shipping_city,
                'state': shipping_address.shipping_state or '',
                'zipcode': shipping_address.shipping_zipcode or '',
                'country': shipping_address.shipping_country
            }
            request.session['delivery_option'] = {
                'name': selected_delivery.name,
                'price': float(selected_delivery.price),
                'estimated_days': selected_delivery.estimated_days
            }
            request.session['payment_method'] = new_order.get_payment_method_display()
            logger.debug("Redirecting to payment_success")

            # Send Telegram notification
            logger.info(f"About to send Telegram notification for order {new_order.id}")
            try:
                send_telegram_notification(new_order, order_items, shipping_address, selected_delivery, payment_form.cleaned_data['payment_method'])
                logger.info(f"Telegram notification sent successfully for order {new_order.id}")
            except Exception as e:
                logger.error(f"Error in Telegram notification for order {new_order.id}: {str(e)}")
            
            logger.info(f"Redirecting to payment_success for order {new_order.id}")
            return redirect('payment_success')

        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            messages.error(request, f"Error processing order: {str(e)}")
            return render(request, "payment/checkout.html", {
                'order': order,
                'items': items,
                'delivery_options': delivery_options,
                'selected_delivery_id': selected_delivery_id,
                'shipping_form': shipping_form,
                'payment_form': payment_form,
                'qr_code': qr_code
            })

    return render(request, "payment/checkout.html", {
        'order': order,
        'items': items,
        'delivery_options': delivery_options,
        'selected_delivery_id': selected_delivery_id,
        'shipping_form': shipping_form,
        'payment_form': payment_form,
        'qr_code': qr_code
    })

def send_telegram_notification(order, order_items, shipping_address, delivery_option, payment_method):
    """
    Send order notification to Telegram group
    """
    try:
        bot_token = '7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc'
        chat_id = '-4862435107'  # Bot Get me Shop group
        
        # Calculate total items
        total_items = sum(item.quantity for item in order_items)
        
        # Format a concise message for group
        message = f"🛒 *NEW ORDER #{order.id}*\n\n"
        message += f"💰 *Total:* ${order.amount_paid:.2f}\n"
        message += f"📦 *Items:* {total_items} item{'s' if total_items != 1 else ''}\n"
        message += f"👤 *Customer:* {shipping_address.shipping_full_name}\n"
        message += f"📧 *Email:* {shipping_address.shipping_email}\n"
        message += f"🚚 *Delivery:* {delivery_option.name}\n"
        message += f"💳 *Payment:* {payment_method}\n\n"
        
        # List items briefly
        message += f"📋 *Order Items:*\n"
        for item in order_items:
            message += f"• {item.product.name} x{item.quantity}\n"
        
        message += f"\n📍 *Address:* {shipping_address.shipping_city}, {shipping_address.shipping_country}"
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram notification sent successfully for order {order.id}")
        else:
            logger.error(f"Failed to send Telegram notification: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")

def payment_success(request):
    return render(request, "payment/payment_success.html", {
        'order_id': request.session.get('order_id', 'N/A'),
        'order_items': request.session.get('order_items', []),
        
        'shipping_address': request.session.get('shipping_address', {}),
        'delivery_option': request.session.get('delivery_option', {}),
        'payment_method': request.session.get('payment_method', 'N/A')
    })
    
def payment_view(request):
    form = PaymentForm()
    qr_code = form.get_qr_code() if request.POST.get('payment_method') == 'bank_transfer' else None
    return render(request, 'payment/payment_form.html', {'form': form, 'qr_code': qr_code})
@login_required(login_url='/register/')
def customer_invoice_detail(request, order_id):
    """
    View to display detailed invoice information for a specific order.
    Accessible only to the user who owns the order or via email match.
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Security check: Ensure the order belongs to the logged-in user
    if order.user != request.user and (not order.shipping_address or order.shipping_address.shipping_email != request.user.email):
        messages.error(request, "You do not have permission to view this invoice.")
        return redirect('customer_invoice_list')
    
    # Fetch order items
    items = OrderItem.objects.filter(order=order).select_related('product')
    
    context = {
        'order': order,
        'items': items,
    }
    
    return render(request, 'payment/customer_invoice_detail.html', context)
@login_required(login_url='/register/')
def customer_invoice_list(request):
    email = request.GET.get('email')
    orders = []

    # Use logged-in user's email if no email is provided in GET request
    if not email and request.user.is_authenticated:
        email = request.user.email

    if email:
        orders = Order.objects.filter(shipping_address__shipping_email=email).select_related('shipping_address', 'delivery_option').prefetch_related('orderitem_set__product')
        if not orders:
            messages.info(request, 'No invoices found for this email address.')

    context = {
        'orders': orders,
        'email': email
    }
    return render(request, 'payment/customer_invoice_list.html', context)

@login_required(login_url='/register/')
def test_telegram_notification(request):
    """
    Test endpoint to manually trigger a Telegram notification
    """
    try:
        # Create test data
        test_order = type('TestOrder', (), {
            'id': 999,
            'amount_paid': 299.99
        })()
        
        test_shipping = type('TestShipping', (), {
            'shipping_full_name': 'Test Customer',
            'shipping_email': 'test@example.com',
            'shipping_city': 'New York',
            'shipping_country': 'United States'
        })()
        
        test_delivery = type('TestDelivery', (), {
            'name': 'Express Delivery'
        })()
        
        test_items = [
            type('TestItem', (), {
                'product': type('TestProduct', (), {'name': 'iPhone 15 Pro'})(),
                'quantity': 1,
                'price': 299.99
            })()
        ]
        
        # Send test notification
        send_telegram_notification(test_order, test_items, test_shipping, test_delivery, 'Credit Card')
        
        messages.success(request, 'Test Telegram notification sent successfully!')
        return redirect('payment_success')
        
    except Exception as e:
        messages.error(request, f'Error sending test notification: {str(e)}')
        return redirect('home')