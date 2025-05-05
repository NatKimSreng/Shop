from django.urls import path

from .import views


urlpatterns = [
        #Leave as empty string for base url
	path ('', views.home, name="home"),
	path('store/', views.store, name="store"),
	path('checkout/', views.checkout, name="checkout"),
	path('login/', views.loginPage, name="login"),
	path('logout/', views.logoutUser, name="logout"),
	path('register/', views.registerPage, name="register"),
 	path('update_password/', views.update_password, name="update_password"),
	path('update_user/', views.update_user, name="update_user"),
	path('update_info/', views.update_info, name="update_info"),
	path('product/<int:pk>/', views.product, name="product"),
	path('category/<str:foo>/', views.category, name="category"),
	path('search/', views.search , name="search")
]