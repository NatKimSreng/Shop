from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .cart import Cart
from store.models import Product

def cart_summary(request):
    cart = Cart(request)
    order = {
        'get_cart_items': cart.__len__(),
        'get_cart_total': float(cart.get_total_price())  # Ensure float for JSON
    }
    items = [
        {
            'product': {
                'id': product_id,
                'name': product.name,
                'price': float(item['price']),
                'imageURL': product.imageURL
            },
            'quantity': item['quantity'],
            'get_total': float(item['price']) * item['quantity']
        }
        for product_id, item in cart.cart.items()
        for product in [get_object_or_404(Product, id=int(product_id))]
    ]
    return render(request, "cart_summary.html", {'order': order, 'items': items})

def cart_add(request):
    cart = Cart(request)

    if request.POST.get('action') == 'post':
        try:
            product_id = request.POST.get('product_id')
            product_qty = request.POST.get('product_qty')

            if not product_id or not product_qty:
                return JsonResponse({'error': 'Product ID and quantity are required'}, status=400)

            product_id = int(product_id)
            product_qty = int(product_qty)

            if product_qty < 1:
                return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)

            product = get_object_or_404(Product, id=product_id)
            if not product.Is_sale:
                return JsonResponse({'error': 'Product is out of stock'}, status=400)

            cart.add(product=product, quantity=product_qty)
            cart_quantity = cart.__len__()
            cart_total = float(cart.get_total_price())

            return JsonResponse({'qty': cart_quantity, 'cart_total': cart_total})

        except ValueError:
            return JsonResponse({'error': 'Invalid product ID or quantity'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid action or request'}, status=400)

def cart_update(request):
    cart = Cart(request)

    if request.POST.get('action') == 'post':
        try:
            product_id = request.POST.get('product_id')
            action = request.POST.get('action_type')  # 'add' or 'remove'

            if not product_id or not action:
                return JsonResponse({'error': 'Product ID and action are required'}, status=400)

            product_id = int(product_id)
            product = get_object_or_404(Product, id=product_id)

            current_qty = cart.cart.get(str(product_id), {'quantity': 0})['quantity']
            if action == 'add':
                if not product.Is_sale:
                    return JsonResponse({'error': 'Product is out of stock'}, status=400)
                cart.add(product=product, quantity=1)
            elif action == 'remove':
                cart.update(product=product, quantity=current_qty - 1)

            cart_quantity = cart.__len__()
            cart_total = float(cart.get_total_price())
            item_quantity = cart.cart.get(str(product_id), {'quantity': 0})['quantity']

            return JsonResponse({
                'qty': cart_quantity,
                'item_quantity': item_quantity,
                'cart_total': cart_total,
                'success': True,
            })

        except ValueError:
            return JsonResponse({'error': 'Invalid product ID'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid action or request'}, status=400)

def cart_delete(request):
    cart = Cart(request)
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            if not product_id:
                return JsonResponse({'error': 'Product ID is required'}, status=400)
            product_id = int(product_id)
            product = get_object_or_404(Product, id=product_id)
            cart.remove(product=product)
            cart_quantity = cart.__len__()
            cart_total = float(cart.get_total_price() or 0)
            return JsonResponse({
                'qty': cart_quantity,
                'cart_total': cart_total,
                'success': True
            })
        except ValueError:
            return JsonResponse({'error': 'Invalid product ID'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)