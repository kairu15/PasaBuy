from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="market/auth/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("buyer/", views.buyer_dashboard, name="buyer_dashboard"),
    path("buyer/items/", views.item_list, name="item_list"),
    path("buyer/items/<int:item_id>/", views.item_detail, name="item_detail"),
    path("buyer/items/<int:item_id>/add/", views.add_to_cart, name="add_to_cart"),
    path("buyer/items/<int:item_id>/buy-now/", views.buy_now, name="buy_now"),
    path("buyer/cart/", views.cart_view, name="cart"),
    path("buyer/checkout/", views.checkout, name="checkout"),
    path("buyer/orders/", views.my_orders, name="my_orders"),
    path("buyer/profile/", views.profile, name="profile"),
    path("map/", views.map_view, name="map"),
    path("api/location/save/", views.save_location, name="save_location"),
    path("api/location/feed/", views.location_feed, name="location_feed"),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/payment/", views.admin_payment_settings, name="admin_payment_settings"),
    path("admin-panel/items/", views.admin_items, name="admin_items"),
    path("admin-panel/items/new/", views.item_create, name="item_create"),
    path("admin-panel/items/<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("admin-panel/items/<int:item_id>/delete/", views.item_delete, name="item_delete"),
    path("admin-panel/items/<int:item_id>/sold/", views.item_mark_sold, name="item_mark_sold"),
    path("admin-panel/orders/", views.admin_orders, name="admin_orders"),
    path("admin-panel/orders/<int:order_id>/delete/", views.order_delete, name="order_delete"),
    path("admin-panel/sold-items/", views.admin_sold_items, name="admin_sold_items"),
]
