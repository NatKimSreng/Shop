# payment/forms.py
from django import forms
from .models import ShippingAddress

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
        labels = {
            'shipping_full_name': 'Full Name',
            'shipping_email': 'Email Address',
            'shipping_address1': 'Address Line 1',
            'shipping_address2': 'Address Line 2 (Optional)',
            'shipping_city': 'City',
            'shipping_state': 'State/Province',
            'shipping_zipcode': 'Zip/Postal Code',
            'shipping_country': 'Country'
        }
        widgets = {
            'shipping_full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'required': True
            }),
            'shipping_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'shipping_address1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your primary address',
                'required': True
            }),
            'shipping_address2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, etc. (optional)'
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your city',
                'required': True
            }),
            'shipping_state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your state or province',
                'required': True
            }),
            'shipping_zipcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your zip or postal code',
                'required': True
            }),
            'shipping_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your country',
                'required': True
            }),
        }
  

from django import forms
import qrcode
from io import BytesIO
import base64

class PaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('cod', 'Pay on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'paymentMethod',
            'onchange': 'toggleQRCode()'
        }),
        label='Choose Payment Method'
    )

    def get_qr_code(self):
        """Generate a QR code image for bank transfer."""
        # Sample payment data; replace with your bank details
        payment_data = "Bank: Example Bank\nAccount: 1234567890\nAmount: ${order['grand_total']:.2f}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_data)
        qr.make(fit=True)

        # Create image and encode as base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')