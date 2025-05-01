from django.urls import path

from .import views


urlpatterns = [
        #Leave as empty string for base url
	path('', views.store, name="store"),
	path ('home', views.home, name="home"),
	path('checkout/', views.checkout, name="checkout"),
	path('login/', views.loginPage, name="login"),
	path('logout/', views.logoutUser, name="logout"),
	path('register/', views.registerPage, name="register"),
	path('update_user/', views.update_user, name="update_user"),
	path('update_password/', views.update_password, name="update_password"),
	path('product/<int:pk>/', views.product, name="product"),
	path('category/<str:foo>/', views.category, name="category"),
]