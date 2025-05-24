# payment/admin.py
from django.contrib import admin
from .models import DeliveryOption, ShippingAddress, Order, OrderItem

@admin.register(DeliveryOption)
class DeliveryOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'estimated_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'shipping_full_name', 'shipping_city', 'shipping_country']
    list_filter = ['shipping_city', 'shipping_country']
    search_fields = ['shipping_full_name', 'shipping_email', 'shipping_address1']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'shipping_address', 'delivery_option', 'payment_method', 'amount_paid', 'status', 'date_ordered']
    list_filter = ['status', 'payment_method', 'date_ordered']
    search_fields = ['user__username', 'shipping_address__shipping_full_name']
    readonly_fields = ['date_ordered', 'date_shipped']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'get_total']
    list_filter = ['order__status']
    search_fields = ['product__name', 'order__id']

    def product_name(self, obj):
        return obj.product.name if obj.product else 'N/A'
    product_name.short_description = 'Product'

    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'