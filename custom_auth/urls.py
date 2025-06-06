from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
     path('admin/products/', views.admin_product_list, name='admin_product_list'),
]