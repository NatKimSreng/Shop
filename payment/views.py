from django.shortcuts import render
from store.models import *
# Create your views here.
def payment_success (request):
    return render(request, "payment/payment_success.html",{})