from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Category, Profile
from payment.models import Order, OrderItem, ShippingAddress, DeliveryOption
from django.contrib import messages
from django import forms
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from datetime import timedelta
from functools import wraps

# Role-based permission decorators
def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')
            
            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check user's role
            try:
                user_role = request.user.profile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'Access denied. Required roles: {", ".join(allowed_roles)}')
                    return redirect('admin_dashboard')
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                Profile.objects.create(user=request.user, role='CUSTOMER')
                messages.error(request, 'Access denied. Insufficient permissions.')
                return redirect('admin_dashboard')
        return _wrapped_view
    return decorator

# Role checking functions
def is_admin_or_superuser(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.role in ['ADMIN']
    except Profile.DoesNotExist:
        return False

def is_manager_or_above(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.role in ['ADMIN', 'MANAGER']
    except Profile.DoesNotExist:
        return False

def is_staff_or_above(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.role in ['ADMIN', 'MANAGER', 'STAFF']
    except Profile.DoesNotExist:
        return False

# Custom form for adding/editing products
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'Sale_price', 'quantity', 'Is_sale', 'description', 'image', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'Is_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'Sale_price': 'Sale Price',
            'quantity': 'Stock Quantity',
            'Is_sale': 'On Sale',
            'image': 'Product Image',
        }

    def clean(self):
        cleaned_data = super().clean()
        sale_price = cleaned_data.get('Sale_price')
        is_sale = cleaned_data.get('Is_sale')
        quantity = cleaned_data.get('quantity', 0)
        
        # Ensure quantity is not negative
        if quantity is not None and quantity < 0:
            self.add_error('quantity', 'Stock quantity cannot be negative.')
        
        # Check if product is on sale but has no sale price
        if is_sale and (sale_price is None or sale_price <= 0):
            self.add_error('Sale_price', 'A valid sale price is required when the product is on sale.')
        
        return cleaned_data

# User Profile Form
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'phone', 'address1', 'address2', 'city', 'state', 'zipcode', 'country']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address1': forms.TextInput(attrs={'class': 'form-control'}),
            'address2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_dashboard(request):
    target_brands = ['Oppo', 'ROG', 'Vivo', 'Samsung', 'Pixel', 'iPhone']
    now = timezone.now()

    # Get filter parameters
    selected_brand = request.GET.get('brand', '')
    selected_status = request.GET.get('status', '')
    selected_date = request.GET.get('date', '')

    # Base queryset for orders
    orders = Order.objects.select_related('user', 'shipping_address', 'delivery_option').prefetch_related('orderitem_set__product')

    # Apply filters
    if selected_brand:
        orders = orders.filter(orderitem__product__category__name=selected_brand)
    if selected_status:
        orders = orders.filter(status=selected_status)
    if selected_date:
        if selected_date == 'today':
            orders = orders.filter(date_ordered__date=now.date())
        elif selected_date == 'past_7_days':
            orders = orders.filter(date_ordered__gte=now - timedelta(days=7))
        elif selected_date == 'this_month':
            orders = orders.filter(date_ordered__year=now.year, date_ordered__month=now.month)
        elif selected_date == 'this_year':
            orders = orders.filter(date_ordered__year=now.year)

    # Calculate total order amounts
    total_today = orders.filter(
        date_ordered__date=now.date()
    ).aggregate(total=Sum('amount_paid'))['total'] or 0.0
    total_month = orders.filter(
        date_ordered__year=now.year, date_ordered__month=now.month
    ).aggregate(total=Sum('amount_paid'))['total'] or 0.0
    total_year = orders.filter(
        date_ordered__year=now.year
    ).aggregate(total=Sum('amount_paid'))['total'] or 0.0

    # Calculate order counts by status
    status_counts = orders.values('status').annotate(count=Count('id')).order_by('status')
    status_data = {
        'PENDING': 0,
        'SHIPPED': 0,
        'DELIVERED': 0,
        'CANCELLED': 0
    }
    for item in status_counts:
        status_data[item['status']] = item['count']

    # Product sales data
    products = Product.objects.filter(category__name__in=target_brands)
    if selected_brand:
        products = products.filter(category__name=selected_brand)
    product_sales = []
    for product in products:
        product_orders = orders.filter(
            orderitem__product=product,
            status__in=['SHIPPED', 'DELIVERED']
        )
        total_amount = product_orders.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0.0
        product_sales.append({
            'product': product,
            'category': product.category.name if product.category else 'N/A',
            'price': product.price or 0.0,
            'sale_price': product.Sale_price or 0.0,
            'is_sale': product.Is_sale,
            'amount_paid': total_amount
        })

    # Sales by brand data
    sales_by_brand = {}
    for brand in target_brands:
        brand_orders = orders.filter(
            orderitem__product__category__name=brand,
            status__in=['SHIPPED', 'DELIVERED']
        )
        total_sales = brand_orders.aggregate(total=Sum('amount_paid'))['total'] or 0.0
        sales_by_brand[brand] = total_sales

    # Top products (by sales amount)
    top_products = sorted(product_sales, key=lambda x: x['amount_paid'], reverse=True)[:5]

    # Recent orders (last 5)
    recent_orders = orders.order_by('-date_ordered')[:5]

    # Recent users (last 5)
    recent_users = User.objects.order_by('-date_joined')[:5]

    # Sales by category (pie chart) - limit to top 6
    categories = Category.objects.all()
    sales_by_category = []
    for cat in categories:
        cat_orders = orders.filter(orderitem__product__category=cat, status__in=['SHIPPED', 'DELIVERED'])
        total_sales = cat_orders.aggregate(total=Sum('amount_paid'))['total'] or 0.0
        sales_by_category.append({'category': cat.name, 'total': total_sales})
    
    # Sort by total sales and limit to top 6
    sales_by_category = sorted(sales_by_category, key=lambda x: x['total'], reverse=True)[:6]

    # --- Dashboard summary stats ---
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status__in=['SHIPPED', 'DELIVERED']).aggregate(total=Sum('amount_paid'))['total'] or 0.0

    # --- Notifications ---
    low_stock_products = Product.objects.filter(quantity__lte=5).order_by('quantity')
    new_orders_count = Order.objects.filter(status='PENDING').count()

    context = {
        'product_sales': product_sales,
        'sales_by_brand': sales_by_brand,
        'target_brands': target_brands,
        'total_today': total_today,
        'total_month': total_month,
        'total_year': total_year,
        'status_counts': status_data,
        'selected_brand': selected_brand,
        'selected_status': selected_status,
        'selected_date': selected_date,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'sales_by_category': sales_by_category,
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'low_stock_products': low_stock_products,
        'new_orders_count': new_orders_count,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_order_list(request):
    target_brands = ['Oppo', 'ROG', 'Vivo', 'Samsung', 'Pixel', 'iPhone']
    orders = Order.objects.select_related('user', 'shipping_address', 'delivery_option').prefetch_related('orderitem_set__product')
    orders = Order.objects.all().order_by('-id')
    
    # Apply filters
    selected_brand = request.GET.get('brand', '')
    selected_status = request.GET.get('status', '')
    selected_payment = request.GET.get('payment', '')
    selected_date = request.GET.get('date', '')

    if selected_brand:
        orders = orders.filter(orderitem__product__category__name=selected_brand)
    if selected_status:
        orders = orders.filter(status=selected_status)
    if selected_payment:
        orders = orders.filter(payment_method=selected_payment)
    if selected_date:
        now = timezone.now()
        if selected_date == 'today':
            orders = orders.filter(date_ordered__date=now.date())
        elif selected_date == 'past_7_days':
            orders = orders.filter(date_ordered__gte=now - timedelta(days=7))
        elif selected_date == 'this_month':
            orders = orders.filter(date_ordered__year=now.year, date_ordered__month=now.month)
        elif selected_date == 'this_year':
            orders = orders.filter(date_ordered__year=now.year)

    # Status counts for stats bar
    status_counts = {
        'PENDING': orders.filter(status='PENDING').count(),
        'SHIPPED': orders.filter(status='SHIPPED').count(),
        'DELIVERED': orders.filter(status='DELIVERED').count(),
        'CANCELLED': orders.filter(status='CANCELLED').count(),
    }

    context = {
        'orders': orders,
        'target_brands': target_brands,
        'selected_brand': selected_brand,
        'selected_status': selected_status,
        'selected_payment': selected_payment,
        'selected_date': selected_date,
        'status_counts': status_counts,
    }
    return render(request, 'admin_order.html', context)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user', 'shipping_address', 'delivery_option').prefetch_related('orderitem_set__product'),
        id=order_id
    )
    if request.method == 'POST':
        status = request.POST.get('status')
        valid_statuses = ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
        if not status:
            messages.error(request, 'Status parameter is missing.')
            return redirect('admin_order_detail', order_id=order_id)
        if status in valid_statuses:
            order.status = status
            if status == 'SHIPPED':
                order.date_shipped = timezone.now()
            order.save()
            messages.success(request, f'Order {order.id} status updated to {status}.')
            return redirect('admin_order_detail', order_id=order_id)
        else:
            messages.error(request, f'Invalid status: {status}.')
    context = {
        'order': order,
        'items': order.orderitem_set.all(),
    }
    return render(request, 'admin_order_detail.html', context)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
@require_POST
def admin_order_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status')
    valid_statuses = ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
    if not status:
        messages.error(request, 'Status parameter is missing.')
        return redirect('admin_order_list')
    if status in valid_statuses:
        order.status = status
        if status == 'SHIPPED':
            order.date_shipped = timezone.now()
        order.save()
        messages.success(request, f'Order {order.id} status updated to {status}.')
    else:
        messages.error(request, f'Invalid status: {status}.')
    return redirect('admin_order_detail', order_id=order_id)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock', '')
    sale_status = request.GET.get('sale', '')

    # Search
    if search_query:
        products = products.filter(name__icontains=search_query)
    # Filter by category
    if category_id:
        products = products.filter(category_id=category_id)
    # Filter by stock status
    if stock_status == 'in':
        products = products.filter(quantity__gt=0)
    elif stock_status == 'out':
        products = products.filter(quantity=0)
    # Filter by sale status
    if sale_status == '1':
        products = products.filter(Is_sale=True)
    elif sale_status == '0':
        products = products.filter(Is_sale=False)

    # Bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_products')
        if selected_ids:
            selected_products = Product.objects.filter(id__in=selected_ids)
            if action == 'set_sale':
                selected_products.update(Is_sale=True)
                messages.success(request, f"Set {selected_products.count()} products on sale.")
            elif action == 'unset_sale':
                selected_products.update(Is_sale=False)
                messages.success(request, f"Removed sale from {selected_products.count()} products.")
            elif action == 'delete':
                count = selected_products.count()
                selected_products.delete()
                messages.success(request, f"Deleted {count} products.")
            elif action == 'restock':
                restock_qty = int(request.POST.get('restock_qty', 0))
                for product in selected_products:
                    product.quantity += restock_qty
                    product.save()
                messages.success(request, f"Restocked {selected_products.count()} products by {restock_qty} units each.")
            return redirect('admin_product_list')
        else:
            messages.warning(request, "No products selected for bulk action.")

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'category_id': category_id,
        'stock_status': stock_status,
        'sale_status': sale_status,
    }
    return render(request, 'admin_product_list.html', context)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_product(request):
    products = Product.objects.all()
    return render(request, 'admin_product.html', {'products': products})

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('admin_product_list')
        else:
            messages.error(request, 'Error adding product. Please check the form.')
    else:
        form = ProductForm()
    return render(request, 'admin_product_form.html', {'form': form, 'title': 'Add Product'})

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_product_list')
        else:
            messages.error(request, 'Error updating product. Please check the form.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('admin_product_list')
    return render(request, 'admin_product_confirm_delete.html', {'product': product})

def is_admin(user):
    return user.is_superuser

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_user_list(request):
    users = User.objects.select_related('profile').all()
    search_query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    is_active = request.GET.get('is_active', '')
    is_staff = request.GET.get('is_staff', '')

    # Search
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | Q(email__icontains=search_query)
        )
    # Filter by role
    if role:
        users = users.filter(profile__role=role)
    # Filter by active status
    if is_active in ['1', '0']:
        users = users.filter(is_active=(is_active == '1'))
    # Filter by staff status
    if is_staff in ['1', '0']:
        users = users.filter(is_staff=(is_staff == '1'))

    # Bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_users')
        if selected_ids:
            selected_users = User.objects.filter(id__in=selected_ids)
            if action == 'activate':
                selected_users.update(is_active=True)
                messages.success(request, f"Activated {selected_users.count()} users.")
            elif action == 'deactivate':
                selected_users.update(is_active=False)
                messages.success(request, f"Deactivated {selected_users.count()} users.")
            elif action == 'delete':
                count = selected_users.count()
                selected_users.delete()
                messages.success(request, f"Deleted {count} users.")
            return redirect('admin_user_list')
        else:
            messages.warning(request, "No users selected for bulk action.")

    context = {
        'users': users,
        'search_query': search_query,
        'role': role,
        'is_active': is_active,
        'is_staff': is_staff,
    }
    return render(request, 'user_list.html', context)

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Ensure user has a profile
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Update user fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        
        # Update profile fields
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')
        country = request.POST.get('country')
        
        # Validate role permissions (only admins can assign admin role)
        if role == 'ADMIN' and not request.user.is_superuser and request.user.profile.role != 'ADMIN':
            messages.error(request, 'Only superusers can assign admin role.')
            return redirect('admin_user_edit', pk=pk)
        
        # Update user
        user.username = username
        user.email = email
        user.is_active = is_active
        user.is_staff = is_staff
        user.save()
        
        # Update profile
        profile.role = role
        profile.phone = phone
        profile.address1 = address1
        profile.address2 = address2
        profile.city = city
        profile.state = state
        profile.zipcode = zipcode
        profile.country = country
        profile.save()
        
        messages.success(request, 'User updated successfully')
        return redirect('admin_user_list')
    
    return render(request, 'user_edit.html', {'user': user})

@login_required(login_url='/login/')
@role_required(['ADMIN', 'MANAGER'])
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully')
        return redirect('admin_user_list')
    return render(request, 'user_delete.html', {'user': user})