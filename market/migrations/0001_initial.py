import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Item",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("stock", models.PositiveIntegerField(default=0)),
                ("image_url", models.URLField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("seller_name", models.CharField(blank=True, max_length=120)),
                ("seller_latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("seller_longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("seller_updated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "cart",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="market.cart"),
                ),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="market.item")),
            ],
            options={"unique_together": {("cart", "item")}},
        ),
        migrations.CreateModel(
            name="LocationPing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "subject_type",
                    models.CharField(
                        choices=[("BUYER", "Buyer"), ("ADMIN", "Admin"), ("SELLER", "Seller")],
                        max_length=10,
                    ),
                ),
                ("label", models.CharField(max_length=120)),
                ("latitude", models.DecimalField(decimal_places=7, max_digits=10)),
                ("longitude", models.DecimalField(decimal_places=7, max_digits=10)),
                ("address", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_pings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["subject_type", "label"]},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("buyer_name", models.CharField(max_length=120)),
                ("address", models.TextField()),
                ("contact_number", models.CharField(max_length=30)),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                (
                    "payment_method",
                    models.CharField(choices=[("GCASH", "GCash"), ("COD", "Cash on Delivery")], max_length=10),
                ),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PAID", "Paid"),
                            ("DELIVERED", "Delivered"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=12,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_name", models.CharField(max_length=160)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="market.item")),
                (
                    "order",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="market.order"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[("BUYER", "Buyer"), ("ADMIN", "Admin"), ("SELLER", "Seller")],
                        default="BUYER",
                        max_length=10,
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("address", models.TextField()),
                ("contact_number", models.CharField(max_length=30)),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("location_updated_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
