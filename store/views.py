from django.shortcuts import render, redirect 
from .models import *  
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
# Create your views here.

def update_info(request):
    if request.user.is_authenticated:
        current_user = Profile.objects.get(user__id=request.user.id)
        form = UserInfoForm(request.POST or None , instance=current_user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated')
            return redirect('store')
        return render(request, 'store/update_info.html',{'form': form})
    else:
        messages.error(request, 'You need to be logged in to update your profile')
        return redirect('login')

def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None , instance=current_user)
        
        if user_form.is_valid():
            user_form.save()
            login(request, current_user)
            messages.success(request, 'User updated')
            return redirect('store')
        return render(request, 'store/update_user.html', {'user_form': user_form})
    else:
        messages.error(request, 'You need to be logged in to update your profile')
        return redirect('login')
    return render(request, 'store/update_user.html')
    

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
    
def home(request):
    products = Product.objects.all()
    context = {'products':products}
    return render(request, 'store/home.html', context)

def update_password(request):
    if request.user.is_authenticated:
       current_user = request.user
       if request.method == 'POST':
           form = ChangePasswordForm(current_user, request.POST)
           if form.is_valid():
               form.save()
               messages.success(request, "Password updated successfully")
               login(request, current_user)
               return redirect('update_user')
           else:
               for error in list (form.errors.values()):
                   messages.error(request, error)
                   return redirect('update_password')
       else:
            form = ChangePasswordForm(current_user)
            return render(request, 'store/update_password.html', {'form': form})
    else:
        messages.success(request, "You need to be logged in to update your password")
        return redirect('store')
            