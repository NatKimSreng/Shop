# payment/views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

@login_required
def checkout(request):
    from cart.cart import Cart
    from store.models import Product
    from .forms import ShippingForm, PaymentForm
    from .models import ShippingAddress, Order, OrderItem, DeliveryOption

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
        # Ensure cart_total_raw is a string or number, and clean it
        if isinstance(cart_total_raw, str):
            # Remove any invalid characters or multiple decimals
            cart_total_raw = cart_total_raw.replace(',', '').split('.')[0] + '.' + ''.join(cart_total_raw.split('.')[1:])[:2]
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
                items.append({
                    'product': {
                        'id': pid,
                        'name': product.name,
                        'price': float(cart.cart[str(pid)]['price']),
                        'imageURL': product.imageURL
                    },
                    'quantity': cart.cart[str(pid)]['quantity'],
                    'get_total': float(cart.cart[str(pid)]['price']) * cart.cart[str(pid)]['quantity']
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

    if request.method == 'POST' and shipping_form.is_valid() and payment_form.is_valid():
        try:
            # Save shipping address
            shipping_address = shipping_form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()

            # Create Order
            new_order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                delivery_option=selected_delivery,
                payment_method=payment_form.cleaned_data['payment_method'],
                amount_paid=order['grand_total']
            )

            # Create OrderItems
            order_items = []
            for product_id, item in cart.cart.items():
                product = product_dict.get(product_id)
                if product:
                    order_item = OrderItem.objects.create(
                        order=new_order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price']
                    )
                    order_items.append(order_item)

            # Clear cart by resetting the session cart
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
            return redirect('payment_success')

        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            return render(request, "payment/checkout.html", {
                'order': order,
                'items': items,
                'delivery_options': delivery_options,
                'selected_delivery_id': selected_delivery_id,
                'shipping_form': shipping_form,
                'payment_form': payment_form,
                'error': f"Error processing order: {str(e)}"
            })

    return render(request, "payment/checkout.html", {
        'order': order,
        'items': items,
        'delivery_options': delivery_options,
        'selected_delivery_id': selected_delivery_id,
        'shipping_form': shipping_form,
        'payment_form': payment_form
    })

def payment_success(request):
    return render(request, "payment/payment_success.html", {
        'order_id': request.session.get('order_id', 'N/A'),
        'order_items': request.session.get('order_items', []),
        'shipping_address': request.session.get('shipping_address', {}),
        'delivery_option': request.session.get('delivery_option', {}),
        'payment_method': request.session.get('payment_method', 'N/A')
    })