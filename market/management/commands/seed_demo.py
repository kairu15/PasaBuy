from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from market.models import Item, UserProfile


class Command(BaseCommand):
    help = "Create demo admin, buyer, and inventory records for local testing."

    def handle(self, *args, **options):
        admin, created_admin = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@pasabuy.local"},
        )
        if created_admin:
            admin.set_password("Admin12345!")
            admin.save()
        UserProfile.objects.update_or_create(
            user=admin,
            defaults={
                "role": UserProfile.Role.ADMIN,
                "name": "PasaBuy Admin",
                "address": "Admin hub",
                "contact_number": "09000000000",
                "gcash_name": "PasaBuy Admin",
                "gcash_number": "09171234567",
            },
        )

        buyer, created_buyer = User.objects.get_or_create(username="buyer", defaults={"email": "buyer@pasabuy.local"})
        if created_buyer:
            buyer.set_password("Buyer12345!")
            buyer.save()
        UserProfile.objects.update_or_create(
            user=buyer,
            defaults={
                "role": UserProfile.Role.BUYER,
                "name": "Demo Buyer",
                "address": "Sample delivery address",
                "contact_number": "09170000000",
            },
        )

        sample_items = [
            {
                "name": "Rice Pack 5kg",
                "category": "Grocery",
                "description": "Quality rice pack for family meals.",
                "price": Decimal("320.00"),
                "stock": 25,
                "seller_name": "Market Stall A",
                "seller_latitude": Decimal("14.5995000"),
                "seller_longitude": Decimal("120.9842000"),
            },
            {
                "name": "Fresh Eggs Tray",
                "category": "Grocery",
                "description": "Thirty fresh eggs packed for delivery.",
                "price": Decimal("240.00"),
                "stock": 18,
                "seller_name": "Farm Booth",
                "seller_latitude": Decimal("14.6042000"),
                "seller_longitude": Decimal("120.9822000"),
            },
            {
                "name": "Laundry Detergent",
                "category": "Household",
                "description": "Powder detergent for everyday laundry.",
                "price": Decimal("155.00"),
                "stock": 40,
                "seller_name": "Daily Goods Seller",
                "seller_latitude": Decimal("14.5953000"),
                "seller_longitude": Decimal("120.9901000"),
            },
        ]
        for data in sample_items:
            Item.objects.update_or_create(
                name=data["name"],
                defaults={**data, "is_active": True, "created_by": admin, "seller_updated_at": timezone.now()},
            )

        self.stdout.write(self.style.SUCCESS("Demo data ready. Admin: admin / Admin12345!, Buyer: buyer / Buyer12345!"))
