from django.shortcuts import render, redirect 
from .models import *  
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import SignUpForm
# Create your views here.
def store(request):
	products = Product.objects.all()
	context = {'products':products}
	return render(request, 'store/store.html', context)

def checkout(request):
	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}

	context = {'items':items, 'order':order}
	return render(request, 'store/checkout.html', context)

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'User logged in')
            return redirect('store')
        else:
            messages.error(request, 'Username or password is incorrect')
            return redirect('login')
    else:
        return render(request, 'store/login.html', {})
    
def logoutUser(request):
	logout(request)
	messages.success(request, 'User logged out')
	return redirect ('store')

def registerPage(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'User created')
            return redirect('store')
        else:
            messages.error(request, 'Error creating user')
            return redirect('register')
    else:
        form = SignUpForm()
        context = {'form':form}
        return render(request, 'store/register.html', context)

def product(request, pk):
    product = Product.objects.get(id=pk)
    context = {'product':product}
    return render(request, 'store/product.html', context)

def category(request, foo):
    try:
        category_obj = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category_obj)
        context = {'products': products, 'category': category_obj}
        return render(request, 'store/category.html', context)
    except Category.DoesNotExist:
        messages.error(request, 'Category does not exist')
        return redirect('store')