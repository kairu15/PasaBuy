from django.contrib import admin

from .models import Cart, CartItem, Item, LocationPing, Order, OrderItem, UserProfile


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("item", "item_name", "quantity", "unit_price", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer_name", "payment_method", "status", "total_amount", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("buyer_name", "address", "contact_number")
    inlines = [OrderItemInline]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "seller_name")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description", "seller_name")


admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(LocationPing)

