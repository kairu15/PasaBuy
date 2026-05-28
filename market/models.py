from decimal import Decimal

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    class Role(models.TextChoices):
        BUYER = "BUYER", "Buyer"
        ADMIN = "ADMIN", "Admin"
        SELLER = "SELLER", "Seller"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    name = models.CharField(max_length=120)
    address = models.TextField()
    contact_number = models.CharField(max_length=30)
    gcash_name = models.CharField(max_length=120, blank=True)
    gcash_number = models.CharField(max_length=30, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Item(models.Model):
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    image = models.FileField(
        upload_to="items/",
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "gif", "webp"])],
    )
    is_active = models.BooleanField(default=True)
    seller_name = models.CharField(max_length=120, blank=True)
    seller_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    seller_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    seller_updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_items",
    )
    manual_sold_order = models.OneToOneField(
        "Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_sold_item",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def available(self):
        return self.is_active and self.stock > 0


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_amount(self):
        return sum((line.line_total for line in self.items.select_related("item")), Decimal("0.00"))

    @property
    def total_quantity(self):
        return sum(line.quantity for line in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "item")

    @property
    def line_total(self):
        return self.item.price * self.quantity


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        GCASH = "GCASH", "GCash"
        COD = "COD", "Cash on Delivery"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    buyer_name = models.CharField(max_length=120)
    address = models.TextField()
    contact_number = models.CharField(max_length=30)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    payment_screenshot = models.FileField(
        upload_to="payment_screenshots/",
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "gif", "webp"])],
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.buyer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    item_name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"


class LocationPing(models.Model):
    class SubjectType(models.TextChoices):
        BUYER = "BUYER", "Buyer"
        ADMIN = "ADMIN", "Admin"
        SELLER = "SELLER", "Seller"

    subject_type = models.CharField(max_length=10, choices=SubjectType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="location_pings",
    )
    label = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    address = models.TextField(blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["subject_type", "label"]

    def __str__(self):
        return f"{self.label} - {self.get_subject_type_display()}"
