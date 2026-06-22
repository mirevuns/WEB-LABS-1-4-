from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from .models import Cart, CartItem, Customer, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "created_at")
    search_fields = ("full_name", "email")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
    date_hierarchy = "created_at"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = (CartItemInline,)

    list_display = (
        "id",
        "customer",
        "status_badge",
        "created_at",
        "products_count",
        "total_quantity_display",
        "total_price_display",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer__full_name", "customer__email", "items__product__name")
    date_hierarchy = "created_at"
    list_select_related = ("customer",)

    readonly_fields = ("created_at", "total_price_display", "total_quantity_display")

    fieldsets = (
        (None, {"fields": ("customer", "status")}),
        ("Служебное", {"fields": ("created_at",)}),
        ("Итоги", {"fields": ("total_quantity_display", "total_price_display")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        total_qty = Coalesce(Sum("items__quantity"), 0)
        line_total = ExpressionWrapper(
            F("items__quantity") * F("items__product__price"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        total_price = Coalesce(
            Sum(line_total),
            Value(0, output_field=DecimalField(max_digits=14, decimal_places=2)),
        )
        products_count = Coalesce(Count("items__product", distinct=True), 0)
        return qs.annotate(_total_qty=total_qty, _total_price=total_price, _products_count=products_count)

    @admin.display(description="Товаров (видов)", ordering="_products_count")
    def products_count(self, obj: Cart) -> int:
        return int(getattr(obj, "_products_count", 0))

    @admin.display(description="Кол-во (шт.)", ordering="_total_qty")
    def total_quantity_display(self, obj: Cart) -> int:
        return int(getattr(obj, "_total_qty", obj.total_quantity))

    @admin.display(description="Сумма", ordering="_total_price")
    def total_price_display(self, obj: Cart):
        return getattr(obj, "_total_price", obj.total_price)

    @admin.display(description="Статус")
    def status_badge(self, obj: Cart):
        if obj.status == Cart.Status.INACTIVE:
            return format_html('<span style="padding:2px 8px;border-radius:999px;background:#fee2e2;color:#991b1b;">{}</span>', obj.get_status_display())
        return format_html('<span style="padding:2px 8px;border-radius:999px;background:#dcfce7;color:#166534;">{}</span>', obj.get_status_display())


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ("groups_list",)
    list_filter = BaseUserAdmin.list_filter + ("groups",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).prefetch_related("groups")
        first_group_name = Subquery(
            Group.objects.filter(user=F("pk")).order_by("name").values("name")[:1]
        )
        return qs.annotate(_first_group_name=first_group_name)

    @admin.display(description="Группы", ordering="_first_group_name")
    def groups_list(self, obj: User) -> str:
        return ", ".join(obj.groups.values_list("name", flat=True))
