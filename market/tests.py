import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CartItem, Item, LocationPing, Order, OrderItem, UserProfile


class PasaBuyFlowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="Admin12345!")
        UserProfile.objects.create(
            user=self.admin,
            role=UserProfile.Role.ADMIN,
            name="Admin User",
            address="Admin hub",
            contact_number="09000000000",
            gcash_name="Admin GCash",
            gcash_number="09171234567",
        )
        self.buyer = User.objects.create_user(username="buyer", password="Buyer12345!")
        UserProfile.objects.create(
            user=self.buyer,
            role=UserProfile.Role.BUYER,
            name="Buyer User",
            address="Buyer address",
            contact_number="09170000000",
        )
        self.item = Item.objects.create(
            name="Rice Pack",
            category="Grocery",
            price=Decimal("300.00"),
            stock=10,
            is_active=True,
            seller_name="Seller One",
            seller_latitude=Decimal("14.5995000"),
            seller_longitude=Decimal("120.9842000"),
        )

    def test_buyer_registration_creates_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newbuyer",
                "name": "New Buyer",
                "address": "New address",
                "contact_number": "09990000000",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("buyer_dashboard"))
        profile = UserProfile.objects.get(user__username="newbuyer")
        self.assertEqual(profile.role, UserProfile.Role.BUYER)
        self.assertEqual(profile.address, "New address")

    def test_buyer_cart_checkout_creates_order_and_reduces_stock(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("add_to_cart", args=[self.item.id]), {"quantity": 3})
        self.assertEqual(CartItem.objects.get(cart__user=self.buyer).quantity, 3)

        response = self.client.post(
            reverse("checkout"),
            {
                "buyer_name": "Buyer User",
                "address": "Buyer address",
                "contact_number": "09170000000",
                "latitude": "14.6100000",
                "longitude": "121.0000000",
                "payment_screenshot": SimpleUploadedFile(
                    "gcash-payment.png",
                    b"fake image content",
                    content_type="image/png",
                ),
            },
        )
        self.assertRedirects(response, reverse("buyer_dashboard"))
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.total_amount, Decimal("900.00"))
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertTrue(order.payment_screenshot.name.startswith("payment_screenshots/"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.stock, 7)

    def test_checkout_is_gcash_only_and_shows_admin_gcash_details(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("add_to_cart", args=[self.item.id]), {"quantity": 1})

        response = self.client.get(reverse("checkout"))

        self.assertContains(response, "GCash")
        self.assertContains(response, "Admin GCash")
        self.assertContains(response, "09171234567")
        self.assertContains(response, "GCash payment screenshot")
        self.assertNotContains(response, "Cash on Delivery")

    def test_checkout_requires_gcash_payment_screenshot(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("add_to_cart", args=[self.item.id]), {"quantity": 1})

        response = self.client.post(
            reverse("checkout"),
            {
                "buyer_name": "Buyer User",
                "address": "Buyer address",
                "contact_number": "09170000000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        self.assertFalse(Order.objects.filter(user=self.buyer).exists())

    def test_buy_now_sends_single_item_to_checkout(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("buy_now", args=[self.item.id]))

        self.assertRedirects(response, reverse("checkout"))
        cart_item = CartItem.objects.get(cart__user=self.buyer)
        self.assertEqual(cart_item.item, self.item)
        self.assertEqual(cart_item.quantity, 1)

    def test_admin_dashboard_requires_admin_account(self):
        self.client.force_login(self.buyer)
        buyer_response = self.client.get(reverse("admin_dashboard"))
        self.assertRedirects(buyer_response, reverse("login"))

        self.client.force_login(self.admin)
        admin_response = self.client.get(reverse("admin_dashboard"))
        self.assertContains(admin_response, "Dashboard")

    def test_admin_pages_include_app_sidebar_controls(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertContains(response, "data-sidebar-toggle")
        self.assertContains(response, "data-sidebar-close")
        self.assertContains(response, reverse("admin_orders"))
        self.assertContains(response, "Orders")

    def test_admin_can_update_gcash_payment_details(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_payment_settings"),
            {"gcash_name": "Updated Admin", "gcash_number": "09998887777"},
        )

        self.assertRedirects(response, reverse("admin_payment_settings"))
        self.admin.userprofile.refresh_from_db()
        self.assertEqual(self.admin.userprofile.gcash_name, "Updated Admin")
        self.assertEqual(self.admin.userprofile.gcash_number, "09998887777")

    def test_admin_can_mark_item_as_sold(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("item_mark_sold", args=[self.item.id]))

        self.assertRedirects(response, reverse("admin_items"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.stock, 0)
        self.assertIsNotNone(self.item.manual_sold_order)
        self.assertEqual(self.item.manual_sold_order.total_amount, Decimal("300.00"))
        self.assertTrue(OrderItem.objects.filter(order=self.item.manual_sold_order, item=self.item).exists())

        dashboard = self.client.get(reverse("admin_dashboard"))
        self.assertContains(dashboard, "Sold items")
        self.assertContains(dashboard, '<span class="metric-value">1</span>', html=True)
        self.assertContains(dashboard, "PHP 300.00")

        sold_items = self.client.get(reverse("admin_sold_items"))
        self.assertContains(sold_items, "Rice Pack")
        self.assertContains(sold_items, "Admin Sold")

    def test_zero_stock_item_does_not_count_as_sold_without_sold_action(self):
        self.item.stock = 0
        self.item.save(update_fields=["stock"])
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertContains(response, '<span class="metric-value">0</span>', html=True)
        self.assertContains(response, "Sold items")

    def test_admin_orders_page_shows_order_items_and_payment(self):
        order = Order.objects.create(
            user=self.buyer,
            buyer_name="Buyer User",
            address="Buyer address",
            contact_number="09170000000",
            payment_method=Order.PaymentMethod.GCASH,
            payment_screenshot="payment_screenshots/sample.png",
            total_amount=Decimal("300.00"),
        )
        OrderItem.objects.create(
            order=order,
            item=self.item,
            item_name=self.item.name,
            quantity=1,
            unit_price=self.item.price,
            line_total=self.item.price,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_orders"))

        self.assertContains(response, "Buyer User")
        self.assertContains(response, "Rice Pack")
        self.assertContains(response, "GCash")
        self.assertContains(response, "/media/payment_screenshots/sample.png")

    def test_buyer_my_orders_page_shows_only_their_orders(self):
        other_buyer = User.objects.create_user(username="other", password="Buyer12345!")
        UserProfile.objects.create(
            user=other_buyer,
            role=UserProfile.Role.BUYER,
            name="Other Buyer",
            address="Other address",
            contact_number="09180000000",
        )
        own_order = Order.objects.create(
            user=self.buyer,
            buyer_name="Buyer User",
            address="Buyer address",
            contact_number="09170000000",
            payment_method=Order.PaymentMethod.GCASH,
            payment_screenshot="payment_screenshots/own.png",
            total_amount=Decimal("300.00"),
            status=Order.Status.PAID,
        )
        OrderItem.objects.create(
            order=own_order,
            item=self.item,
            item_name=self.item.name,
            quantity=1,
            unit_price=self.item.price,
            line_total=self.item.price,
        )
        Order.objects.create(
            user=other_buyer,
            buyer_name="Other Buyer",
            address="Other address",
            contact_number="09180000000",
            payment_method=Order.PaymentMethod.GCASH,
            total_amount=Decimal("100.00"),
            status=Order.Status.PAID,
        )
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("my_orders"))

        self.assertContains(response, "Order #")
        self.assertContains(response, "Ordered items")
        self.assertContains(response, "Rice Pack")
        self.assertContains(response, "Qty 1 x PHP 300.00")
        self.assertContains(response, "PHP 300.00")
        self.assertContains(response, "/media/payment_screenshots/own.png")
        self.assertNotContains(response, "Other Buyer")

    def test_admin_can_delete_order(self):
        order = Order.objects.create(
            user=self.buyer,
            buyer_name="Buyer User",
            address="Buyer address",
            contact_number="09170000000",
            payment_method=Order.PaymentMethod.COD,
            total_amount=Decimal("300.00"),
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("order_delete", args=[order.id]))
        self.assertRedirects(response, reverse("admin_dashboard"))
        self.assertFalse(Order.objects.filter(pk=order.id).exists())

    def test_buyer_dashboard_has_clickable_image_preview(self):
        self.item.image = "items/rice-pack.png"
        self.item.save(update_fields=["image"])
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("buyer_dashboard"))

        self.assertContains(response, 'data-image-src="/media/items/rice-pack.png"')
        self.assertContains(response, "data-image-modal")

    def test_buyer_pages_include_app_sidebar_controls(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("buyer_dashboard"))

        self.assertContains(response, "data-sidebar-toggle")
        self.assertContains(response, "data-sidebar-close")
        self.assertContains(response, reverse("my_orders"))
        self.assertContains(response, "My Orders")

    def test_location_save_and_feed_include_buyer_and_seller(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("save_location"),
            data=json.dumps({"latitude": 14.61, "longitude": 121.01}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(LocationPing.objects.filter(user=self.buyer, subject_type=LocationPing.SubjectType.BUYER).exists())

        feed = self.client.get(reverse("location_feed"))
        payload = feed.json()
        types = {entry["type"] for entry in payload["locations"]}
        self.assertIn("BUYER", types)
        self.assertIn("SELLER", types)
