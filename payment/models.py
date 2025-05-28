# payment/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_migrate
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DeliveryOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (${self.price})"

    class Meta:
        verbose_name_plural = "Delivery Options"

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_full_name = models.CharField(max_length=255)
    shipping_email = models.EmailField(max_length=255)
    shipping_address1 = models.CharField(max_length=255)
    shipping_address2 = models.CharField(max_length=255, null=True, blank=True)
    shipping_city = models.CharField(max_length=255)
    shipping_state = models.CharField(max_length=255, null=True, blank=True)
    shipping_zipcode = models.CharField(max_length=255, null=True, blank=True)
    shipping_country = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f'Shipping Address - {self.id}'

    def get_full_address(self):
        parts = [
            self.shipping_full_name,
            self.shipping_address1,
            self.shipping_address2 or "",
            self.shipping_city,
            self.shipping_state or "",
            self.shipping_zipcode or "",
            self.shipping_country
        ]
        return ", ".join(part for part in parts if part)

@receiver(post_save, sender=User)
def create_shipping(sender, instance, created, **kwargs):
    if created:
        try:
            ShippingAddress.objects.create(user=instance)
            logger.info(f"Created ShippingAddress for user {instance.username}")
        except Exception as e:
            logger.error(f"Failed to create ShippingAddress for user {instance.username}: {e}")

@receiver(post_migrate)
def create_default_delivery_options(sender, **kwargs):
    if sender.name == 'payment':
        defaults = [
            {'name': 'Standard', 'price': 5.00, 'estimated_days': 5, 'description': 'Standard delivery within 5 days'},
            {'name': 'Express', 'price': 15.00, 'estimated_days': 2, 'description': 'Express delivery within 2 days'}
        ]
        for option in defaults:
            DeliveryOption.objects.get_or_create(
                name=option['name'],
                defaults={
                    'price': option['price'],
                    'estimated_days': option['estimated_days'],
                    'description': option['description'],
                    'is_active': True
                }
            )
        logger.info("Checked/created default delivery options")

class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PaymentMethodChoices(models.TextChoices):
        COD = 'cod', 'Pay on Delivery'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    delivery_option = models.ForeignKey(DeliveryOption, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.COD)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_ordered = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    date_shipped = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Order - {self.id}'

    def get_total(self):
        item_total = sum(item.get_total() for item in self.orderitem_set.all())
        delivery_cost = self.delivery_option.price if self.delivery_option else 0
        return item_total + delivery_cost
    @property
    def is_paid(self):
        return self.status in [self.StatusChoices.SHIPPED, self.StatusChoices.DELIVERED]
    @property
    def is_cancelled(self):
        return self.status == self.StatusChoices.CANCELLED
    @property
    def is_get_total(self):
        return self.get_total()

@receiver(pre_save, sender=Order)
def set_shipped_date_on_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            obj = sender._default_manager.get(pk=instance.pk)
            if instance.status == 'SHIPPED' and obj.status != 'SHIPPED':
                instance.date_shipped = timezone.now()
                logger.info(f"Set shipped date for order {instance.id}")
        except sender.DoesNotExist:
            logger.warning(f"Order {instance.pk} not found during pre_save")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'OrderItem - {self.id}'

    def get_total(self):
        return self.price * self.quantity