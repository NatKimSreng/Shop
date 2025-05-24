# payment/forms.py
from django import forms
from .models import ShippingAddress

class ShippingForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = [
            'shipping_full_name',
            'shipping_email',
            'shipping_address1',
            'shipping_address2',
            'shipping_city',
            'shipping_state',
            'shipping_zipcode',
            'shipping_country'
        ]
        widgets = {
            'shipping_full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'shipping_address1': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_address2': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('cod', 'Pay on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Method'
    )