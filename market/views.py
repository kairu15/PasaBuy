import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AdminPaymentForm, AdminProfileForm, BuyerProfileForm, BuyerRegistrationForm, CheckoutForm, ItemForm
from .models import Cart, CartItem, Item, LocationPing, Order, OrderItem, UserProfile


def _is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return getattr(getattr(user, "userprofile", None), "role", None) == UserProfile.Role.ADMIN


def _require_admin(request):
    if not _is_admin(request.user):
        messages.error(request, "Admin access is required.")
        return redirect("login")
    return None


def _cart_for(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _admin_payment_profile():
    return (
        UserProfile.objects.filter(role=UserProfile.Role.ADMIN)
        .exclude(gcash_name="")
        .exclude(gcash_number="")
        .order_by("id")
        .first()
    )


def home(request):
    if request.user.is_authenticated:
        if _is_admin(request.user):
            return redirect("admin_dashboard")
        return redirect("buyer_dashboard")
    return redirect("login")


def register(request):
    if request.method == "POST":
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. Please allow GPS permission to update your location.")
            return redirect("buyer_dashboard")
    else:
        form = BuyerRegistrationForm()
    return render(request, "market/auth/register.html", {"form": form})


@login_required
def buyer_dashboard(request):
    if _is_admin(request.user):
        return redirect("admin_dashboard")
    cart = _cart_for(request.user)
    items = Item.objects.filter(is_active=True, stock__gt=0).order_by("-created_at")[:6]
    orders = Order.objects.filter(user=request.user)[:5]
    return render(
        request,
        "market/buyer/dashboard.html",
        {"items": items, "cart": cart, "orders": orders},
    )


@login_required
def item_list(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    items = Item.objects.filter(is_active=True, stock__gt=0)
    if query:
        items = items.filter(name__icontains=query)
    if category:
        items = items.filter(category=category)
    categories = Item.objects.filter(is_active=True).exclude(category="").values_list("category", flat=True).distinct()
    return render(
        request,
        "market/buyer/item_list.html",
        {"items": items, "query": query, "category": category, "categories": categories},
    )


@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id, is_active=True)
    return render(request, "market/buyer/item_detail.html", {"item": item})


@login_required
@require_POST
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, pk=item_id, is_active=True)
    quantity = max(int(request.POST.get("quantity", 1)), 1)
    cart = _cart_for(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item, defaults={"quantity": 0})
    new_quantity = cart_item.quantity + quantity
    if new_quantity > item.stock:
        messages.warning(request, f"Only {item.stock} item(s) are currently in stock.")
        new_quantity = item.stock
    cart_item.quantity = new_quantity
    cart_item.save()
    messages.success(request, f"{item.name} was added to your cart.")
    return redirect(request.POST.get("next") or reverse("cart"))


@login_required
@require_POST
def buy_now(request, item_id):
    item = get_object_or_404(Item, pk=item_id, is_active=True, stock__gt=0)
    cart = _cart_for(request.user)
    cart.items.all().delete()
    CartItem.objects.create(cart=cart, item=item, quantity=1)
    messages.success(request, f"{item.name} is ready for checkout.")
    return redirect("checkout")


@login_required
def cart_view(request):
    cart = _cart_for(request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        cart_item = get_object_or_404(CartItem, pk=request.POST.get("cart_item_id"), cart=cart)
        if action == "remove":
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
        else:
            quantity = max(int(request.POST.get("quantity", 1)), 1)
            cart_item.quantity = min(quantity, cart_item.item.stock)
            cart_item.save()
            messages.success(request, "Cart updated.")
        return redirect("cart")
    return render(request, "market/buyer/cart.html", {"cart": cart})


@login_required
@transaction.atomic
def checkout(request):
    cart = _cart_for(request.user)
    profile = request.user.userprofile
    if not cart.items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("item_list")

    initial = {
        "buyer_name": profile.name,
        "address": profile.address,
        "contact_number": profile.contact_number,
        "latitude": profile.latitude,
        "longitude": profile.longitude,
    }
    form = CheckoutForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        total = Decimal("0.00")
        for line in cart.items.select_related("item").select_for_update():
            if line.quantity > line.item.stock:
                messages.error(request, f"{line.item.name} does not have enough stock.")
                return redirect("cart")
            total += line.line_total

        order = Order.objects.create(
            user=request.user,
            buyer_name=form.cleaned_data["buyer_name"],
            address=form.cleaned_data["address"],
            contact_number=form.cleaned_data["contact_number"],
            latitude=form.cleaned_data.get("latitude") or profile.latitude,
            longitude=form.cleaned_data.get("longitude") or profile.longitude,
            payment_method=Order.PaymentMethod.GCASH,
            payment_screenshot=form.cleaned_data["payment_screenshot"],
            total_amount=total,
            status=Order.Status.PAID,
        )
        for line in cart.items.select_related("item"):
            OrderItem.objects.create(
                order=order,
                item=line.item,
                item_name=line.item.name,
                quantity=line.quantity,
                unit_price=line.item.price,
                line_total=line.line_total,
            )
            line.item.stock = F("stock") - line.quantity
            line.item.save(update_fields=["stock"])
        cart.items.all().delete()
        messages.success(request, f"Order #{order.pk} placed successfully.")
        return redirect("buyer_dashboard")

    return render(
        request,
        "market/buyer/checkout.html",
        {"form": form, "cart": cart, "payment_profile": _admin_payment_profile()},
    )


@login_required
def my_orders(request):
    if _is_admin(request.user):
        return redirect("admin_orders")
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "market/buyer/my_orders.html", {"orders": orders})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"name": request.user.username, "address": "", "contact_number": ""},
    )
    form = BuyerProfileForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    return render(request, "market/buyer/profile.html", {"form": form, "profile": profile_obj})


@login_required
def map_view(request):
    return render(request, "market/map.html")


@login_required
@require_POST
def save_location(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        latitude = Decimal(str(payload["latitude"]))
        longitude = Decimal(str(payload["longitude"]))
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid location payload."}, status=400)

    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"name": request.user.username, "address": "", "contact_number": ""},
    )
    profile_obj.latitude = latitude
    profile_obj.longitude = longitude
    profile_obj.location_updated_at = timezone.now()
    if _is_admin(request.user):
        profile_obj.role = UserProfile.Role.ADMIN
    profile_obj.save()

    subject = LocationPing.SubjectType.ADMIN if _is_admin(request.user) else LocationPing.SubjectType.BUYER
    LocationPing.objects.filter(user=request.user, subject_type=subject).delete()
    LocationPing.objects.create(
        user=request.user,
        subject_type=subject,
        label=profile_obj.name or request.user.username,
        latitude=latitude,
        longitude=longitude,
        address=profile_obj.address,
    )
    return JsonResponse({"ok": True})


@login_required
def location_feed(request):
    pings = list(LocationPing.objects.select_related("user").all())
    people = [
        {
            "type": ping.subject_type,
            "label": ping.label,
            "latitude": float(ping.latitude),
            "longitude": float(ping.longitude),
            "address": ping.address,
            "updated_at": ping.updated_at.isoformat(),
        }
        for ping in pings
    ]
    sellers = []
    for item in Item.objects.filter(is_active=True, seller_latitude__isnull=False, seller_longitude__isnull=False):
        sellers.append(
            {
                "type": "SELLER",
                "label": item.seller_name or f"Seller for {item.name}",
                "latitude": float(item.seller_latitude),
                "longitude": float(item.seller_longitude),
                "address": item.name,
                "updated_at": (item.seller_updated_at or item.updated_at).isoformat(),
            }
        )
    return JsonResponse({"locations": people + sellers})


@login_required
def admin_dashboard(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    sales_by_day = (
        Order.objects.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("total_amount"), orders=Count("id"))
        .order_by("-day")[:7]
    )
    context = {
        "total_sales_today": today_orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00"),
        "orders_today": today_orders.count(),
        "active_items": Item.objects.filter(is_active=True).count(),
        "sold_items": Item.objects.filter(manual_sold_order__isnull=False).count(),
        "low_stock": Item.objects.filter(is_active=True, stock__lte=5).order_by("stock")[:8],
        "sales_by_day": sales_by_day,
        "recent_orders": Order.objects.select_related("user")[:8],
    }
    return render(request, "market/admin/dashboard.html", context)


@login_required
def admin_payment_settings(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": UserProfile.Role.ADMIN,
            "name": request.user.username,
            "address": "",
            "contact_number": "",
        },
    )
    profile_obj.role = UserProfile.Role.ADMIN
    form = AdminPaymentForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "GCash payment details updated.")
        return redirect("admin_payment_settings")
    return render(request, "market/admin/payment_settings.html", {"form": form})


@login_required
def admin_profile(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": UserProfile.Role.ADMIN,
            "name": request.user.username,
            "address": "",
            "contact_number": "",
        },
    )
    profile_obj.role = UserProfile.Role.ADMIN
    form = AdminProfileForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Admin profile updated.")
        return redirect("admin_profile")
    return render(request, "market/admin/profile.html", {"form": form, "profile": profile_obj})


@login_required
def admin_items(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    query = request.GET.get("q", "").strip()
    stock_filter = request.GET.get("stock", "")
    items = Item.objects.all()
    if query:
        items = items.filter(name__icontains=query)
    if stock_filter == "low":
        items = items.filter(stock__lte=5)
    elif stock_filter == "out":
        items = items.filter(stock=0)
    elif stock_filter == "inactive":
        items = items.filter(is_active=False)
    return render(request, "market/admin/items.html", {"items": items, "query": query, "stock_filter": stock_filter})


@login_required
def item_create(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    form = ItemForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Item added.")
        return redirect("admin_items")
    return render(request, "market/admin/item_form.html", {"form": form, "title": "Add Item"})


@login_required
def item_edit(request, item_id):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    item = get_object_or_404(Item, pk=item_id)
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Item updated.")
        return redirect("admin_items")
    return render(request, "market/admin/item_form.html", {"form": form, "title": "Edit Item", "item": item})


@login_required
@require_POST
def item_delete(request, item_id):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    item = get_object_or_404(Item, pk=item_id)
    item.delete()
    messages.success(request, "Item deleted.")
    return redirect("admin_items")


@login_required
@require_POST
@transaction.atomic
def item_mark_sold(request, item_id):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    item = get_object_or_404(Item.objects.select_for_update(), pk=item_id)
    if item.manual_sold_order_id:
        messages.info(request, f"{item.name} is already recorded as sold.")
        return redirect("admin_items")

    quantity = 1
    total = item.price * quantity
    profile_obj = getattr(request.user, "userprofile", None)
    order = Order.objects.create(
        user=request.user,
        buyer_name="Admin Sold",
        address="Admin inventory sale",
        contact_number=getattr(profile_obj, "contact_number", ""),
        payment_method=Order.PaymentMethod.GCASH,
        total_amount=total,
        status=Order.Status.PAID,
    )
    OrderItem.objects.create(
        order=order,
        item=item,
        item_name=item.name,
        quantity=quantity,
        unit_price=item.price,
        line_total=total,
    )
    item.stock = 0
    item.manual_sold_order = order
    item.save(update_fields=["stock", "manual_sold_order", "updated_at"])
    messages.success(request, f"{item.name} marked as sold and added to sales.")
    return redirect("admin_items")


@login_required
def admin_orders(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    query = request.GET.get("q", "").strip()
    orders = Order.objects.prefetch_related("items").select_related("user")
    if query:
        orders = orders.filter(buyer_name__icontains=query)
    return render(
        request,
        "market/admin/orders.html",
        {
            "orders": orders,
            "query": query,
        },
    )


@login_required
@require_POST
def order_delete(request, order_id):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    order = get_object_or_404(Order, pk=order_id)
    order_label = f"Order #{order.pk}"
    order.delete()
    messages.success(request, f"{order_label} deleted.")
    return redirect(request.POST.get("next") or "admin_dashboard")


@login_required
def admin_sold_items(request):
    blocked = _require_admin(request)
    if blocked:
        return blocked
    date = request.GET.get("date", "")
    sold_items = OrderItem.objects.select_related("order", "item").order_by("-order__created_at")
    if date:
        sold_items = sold_items.filter(order__created_at__date=date)
    totals = sold_items.aggregate(quantity=Sum("quantity"), amount=Sum("line_total"))
    return render(
        request,
        "market/admin/sold_items.html",
        {"sold_items": sold_items, "date": date, "totals": totals},
    )
