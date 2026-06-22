from django.db.models import Prefetch
from django.shortcuts import render

from .models import Cart, CartItem


def carts_list(request):
    carts = (
        Cart.objects.select_related("customer")
        .prefetch_related(
            Prefetch("items", queryset=CartItem.objects.select_related("product").order_by("id"))
        )
        .order_by("-created_at", "-id")
    )
    return render(request, "store/carts_list.html", {"carts": carts})
