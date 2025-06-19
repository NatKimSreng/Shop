from django.contrib import admin

# Register your models here.
from .models import *
from django.contrib.auth.models import User

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ['name']
	search_fields = ['name']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ['fisrt_name', 'last_name', 'email', 'phone']
	search_fields = ['fisrt_name', 'last_name', 'email']
	list_filter = ['fisrt_name', 'last_name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ['name', 'category', 'price', 'Sale_price', 'quantity', 'is_in_stock', 'Is_sale']
	list_filter = ['category', 'Is_sale', 'quantity']
	search_fields = ['name', 'description']
	list_editable = ['quantity', 'price', 'Sale_price', 'Is_sale']
	readonly_fields = ['is_in_stock', 'stock_status']
	
	fieldsets = (
		('Basic Information', {
			'fields': ('name', 'category', 'description', 'image')
		}),
		('Pricing', {
			'fields': ('price', 'Sale_price', 'Is_sale')
		}),
		('Stock Management', {
			'fields': ('quantity', 'is_in_stock', 'stock_status'),
			'description': 'Manage product stock levels'
		}),
	)
	
	def get_queryset(self, request):
		return super().get_queryset(request).select_related('category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ['Product', 'customer', 'quantity', 'date_added', 'status']
	list_filter = ['status', 'date_added']
	search_fields = ['Product__name', 'customer__fisrt_name', 'customer__last_name']
	readonly_fields = ['date_added']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ['user', 'phone', 'city', 'country']
	search_fields = ['user__username', 'user__email', 'phone']
	list_filter = ['country', 'city']

class ProfileInline(admin.StackedInline):
	model = Profile

# Extend User Model
class UserAdmin(admin.ModelAdmin):
	model = User
	field = ["username", "first_name", "last_name", "email"]
	inlines = [ProfileInline]
 
 
admin.site.unregister(User)

# Re-Register the new way
admin.site.register(User, UserAdmin)