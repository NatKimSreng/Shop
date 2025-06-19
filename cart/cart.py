from decimal import Decimal
from django.conf import settings
from store.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity):
        product_id = str(product.id)
        
        # Check if product is in stock
        if not product.is_in_stock:
            return False, "Product is out of stock"
        
        # Check if adding this quantity would exceed available stock
        current_quantity = self.cart.get(product_id, {}).get('quantity', 0)
        total_quantity = current_quantity + quantity
        
        if total_quantity > product.quantity:
            return False, f"Only {product.quantity} items available in stock"
        
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        self.cart[product_id]['quantity'] = total_quantity
        self.save()
        return True, "Product added to cart"

    def update(self, product, quantity):
        product_id = str(product.id)
        
        # Check if product is in stock
        if not product.is_in_stock:
            return False, "Product is out of stock"
        
        # Check if requested quantity exceeds available stock
        if quantity > product.quantity:
            return False, f"Only {product.quantity} items available in stock"
        
        if product_id in self.cart:
            if quantity <= 0:
                self.remove(product)
                return True, "Product removed from cart"
            else:
                self.cart[product_id]['quantity'] = quantity
                self.save()
                return True, "Cart updated"
        return False, "Product not in cart"

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def save(self):
        self.session.modified = True
    
    def get_cart_items(self):
        """Get cart items with product information"""
        items = []
        for product_id, item_data in self.cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({
                    'product': product,
                    'quantity': item_data['quantity'],
                    'price': Decimal(item_data['price']),
                    'total': Decimal(item_data['price']) * item_data['quantity']
                })
            except Product.DoesNotExist:
                # Remove invalid product from cart
                del self.cart[product_id]
        self.save()
        return items
    
    def validate_stock(self):
        """Validate that all items in cart have sufficient stock"""
        errors = []
        for product_id, item_data in self.cart.items():
            try:
                product = Product.objects.get(id=product_id)
                if not product.is_in_stock:
                    errors.append(f"{product.name} is out of stock")
                elif item_data['quantity'] > product.quantity:
                    errors.append(f"Only {product.quantity} {product.name} available in stock")
            except Product.DoesNotExist:
                errors.append(f"Product with ID {product_id} no longer exists")
        return errors