from django.urls import path

from .import views


urlpatterns = [
	path ('payment_success/', views.payment_success, name="payment_success"),
	path('checkout/', views.checkout, name="checkout"),
	path('customer_invoice_detail/<int:order_id>/', views.customer_invoice_detail, name="customer_invoice_detail"),
	path('customer_invoice_list/', views.customer_invoice_list, name="customer_invoice_list"),
]