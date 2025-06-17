from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Category
from payment.models import Order, OrderItem, ShippingAddress, DeliveryOption
from django.contrib import messages
from django import forms
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from datetime import timedelta

# Custom form for adding/editing products
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'Sale_price', 'Is_sale', 'description', 'image', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Is_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'Sale_price': 'Sale Price',
            'Is_sale': 'In Stock',
            'image': 'Product Image',
        }

    def clean(self):
        cleaned_data = super().clean()
        sale_price = cleaned_data.get('Sale_price')
        is_sale = cleaned_data.get('Is_sale')
        if is_sale and (sale_price is None or sale_price <= 0):
            self.add_error('Sale_price', 'A valid sale price is required when the product is in stock.')
        return cleaned_data

# Check if user is admin or superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='/login/')
@user_passes_test(is_admin_or_superuser, login_url='/login/')
def admin_dashboard(request):
    target_brands = ['Oppo', 'ROG', 'Vivo', 'Samsung', 'Pixel', 'iPhone']
    products = Product.objects.filter(category__name__in=target_brands)
    product_sales = []
    for product in products:
        orders = Order.objects.filter(
            orderitem__product=product,
            status__in=['SHIPPED', 'DELIVERED']
        )
        total_amount = orders.aggregate(
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
    sales_by_brand = {}
    for brand in target_brands:
        total_sales = Order.objects.filter(
            orderitem__product__category__name=brand,
            status__in=['SHIPPED', 'DELIVERED']
        ).aggregate(total=Sum('amount_paid'))['total'] or 0.0
        sales_by_brand[brand] = total_sales

    context = {
        'product_sales': product_sales,
        'sales_by_brand': sales_by_brand,
        'target_brands': target_brands,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin_or_superuser, login_url='/login/')
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

    context = {
        'orders': orders,
        'target_brands': target_brands,
        'selected_brand': selected_brand,
        'selected_status': selected_status,
        'selected_payment': selected_payment,
        'selected_date': selected_date,
    }
    return render(request, 'admin_order.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin_or_superuser, login_url='/login/')
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
@user_passes_test(is_admin_or_superuser, login_url='/login/')
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
@user_passes_test(is_admin_or_superuser, login_url='/login/')
def admin_product_list(request):
    products = Product.objects.all()
    return render(request, 'admin_product_list.html', {'products': products})

@login_required(login_url='/login/')
@user_passes_test(is_admin_or_superuser, login_url='/login/')
def admin_product(request):
    products = Product.objects.all()
    return render(request, 'admin_product.html', {'products': products})

@login_required(login_url='/login/')
@user_passes_test(is_admin_or_superuser, login_url='/login/')
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
@user_passes_test(is_admin_or_superuser, login_url='/login/')
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
@user_passes_test(is_admin_or_superuser, login_url='/login/')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('admin_product_list')
    return render(request, 'admin_product_confirm_delete.html', {'product': product})

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        
        user.username = username
        user.email = email
        user.is_active = is_active
        user.is_staff = is_staff
        user.save()
        
        messages.success(request, 'User updated successfully')
        return redirect('admin_user_list')
    
    return render(request, 'user_edit.html', {'user': user})

@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully')
        return redirect('admin_user_list')
    return render(request, 'user_delete.html', {'user': user})