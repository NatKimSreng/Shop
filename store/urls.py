from django.urls import path

from . import views


urlpatterns = [
        #Leave as empty string for base url
	path('', views.store, name="store"),
	path('carts/', views.carts, name="carts"),
	path('checkout/', views.checkout, name="checkout"),
	path('login/', views.loginPage, name="login"),
	path('logout/', views.logoutUser, name="logout"),
	path('register/', views.registerPage, name="register"),
	path('product/<int:pk>/', views.product, name="product"),
	path('category/<str:foo>/', views.category, name="category"),
]