from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Item, Order, UserProfile


class BuyerRegistrationForm(UserCreationForm):
    name = forms.CharField(max_length=120)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    contact_number = forms.CharField(max_length=30)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "name", "address", "contact_number", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.BUYER,
                name=self.cleaned_data["name"],
                address=self.cleaned_data["address"],
                contact_number=self.cleaned_data["contact_number"],
            )
        return user


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("name", "address", "contact_number")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("name", "address", "contact_number")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class AdminPaymentForm(forms.ModelForm):
    gcash_name = forms.CharField(label="GCash account name", max_length=120, required=False)
    gcash_number = forms.CharField(label="GCash number", max_length=30, required=False)

    class Meta:
        model = UserProfile
        fields = ("gcash_name", "gcash_number")


class ItemForm(forms.ModelForm):
    image = forms.FileField(
        required=False,
        label="Item image",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    class Meta:
        model = Item
        fields = (
            "name",
            "category",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
            "seller_name",
            "seller_latitude",
            "seller_longitude",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "seller_latitude": forms.NumberInput(attrs={"step": "0.0000001"}),
            "seller_longitude": forms.NumberInput(attrs={"step": "0.0000001"}),
        }

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock

    def save(self, commit=True):
        item = super().save(commit=False)
        if item.seller_latitude and item.seller_longitude:
            item.seller_updated_at = timezone.now()
        if commit:
            item.save()
            self.save_m2m()
        return item


class CheckoutForm(forms.Form):
    buyer_name = forms.CharField(max_length=120)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    contact_number = forms.CharField(max_length=30)
    payment_screenshot = forms.FileField(
        label="GCash payment screenshot",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a screenshot or photo of your GCash payment confirmation.",
    )
    latitude = forms.DecimalField(max_digits=10, decimal_places=7, required=False, widget=forms.HiddenInput)
    longitude = forms.DecimalField(max_digits=10, decimal_places=7, required=False, widget=forms.HiddenInput)
