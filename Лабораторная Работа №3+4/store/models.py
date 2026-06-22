from django.db import models
from decimal import Decimal


class Customer(models.Model):
    full_name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("Email", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"
        ordering = ["full_name", "id"]

    def __str__(self) -> str:
        return self.full_name


class Product(models.Model):
    name = models.CharField("Название", max_length=200)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активная"
        INACTIVE = "inactive", "Неактивная"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="carts", verbose_name="Покупатель"
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    products = models.ManyToManyField(
        Product, through="CartItem", related_name="carts", verbose_name="Товары", blank=True
    )

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Корзина #{self.pk} — {self.customer}"

    @property
    def total_quantity(self) -> int:
        return int(sum(item.quantity for item in self.items.all()))

    @property
    def total_price(self):
        total = Decimal("0.00")
        for item in self.items.select_related("product").all():
            total += item.quantity * item.product.price
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Корзина")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items", verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзинах"
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="uniq_cart_product")
        ]

    def __str__(self) -> str:
        return f"{self.product} × {self.quantity}"
