from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def badge_available(is_available: bool) -> str:
    if is_available:
        return format_html('<span class="badge badge--ok">В наличии</span>')
    return format_html('<span class="badge badge--no">Нет</span>')


@register.simple_tag
def year_category(year: int) -> str:
    if year < 1950:
        label = "Классика"
    elif year < 2000:
        label = "XX век"
    else:
        label = "Современная"
    return format_html('<span class="chip">{}</span>', label)


@register.simple_tag
def books_count(books) -> str:
    try:
        count = books.count()
    except Exception:
        count = len(books)
    return format_html("<strong>{}</strong>", count)


@register.filter
def rub(price) -> str:
    try:
        value = Decimal(price)
    except (InvalidOperation, TypeError, ValueError):
        return ""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


@register.filter
def initials(author: str) -> str:
    if not author:
        return ""
    parts = [p for p in author.split() if p.strip()]
    if len(parts) == 1:
        return parts[0]
    surname = parts[-1]
    initials = " ".join([f"{p[0].upper()}." for p in parts[:-1] if p])
    return f"{surname} {initials}".strip()

