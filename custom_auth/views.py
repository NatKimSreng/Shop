from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.shortcuts import render
from store.models import Product

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')