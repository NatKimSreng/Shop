from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from store.models import Product

# Check if user is admin or superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='../login/')
@user_passes_test(is_admin_or_superuser, login_url='../login/')
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def admin_product_list(request):
    products = Product.objects.all()
    return render(request, 'admin_product_list.html', {'products': products})