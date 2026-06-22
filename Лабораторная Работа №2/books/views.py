from django.db.models import QuerySet
from django.shortcuts import render
from django.utils import timezone

from .models import Book

SORT_FIELDS = {
    "author": ("author", "title"),
    "-author": ("-author", "title"),
    "title": ("title", "author"),
    "-title": ("-title", "author"),
    "year": ("year", "title"),
    "-year": ("-year", "title"),
    "price": ("price", "title"),
    "-price": ("-price", "title"),
    "created_at": ("created_at",),
    "-created_at": ("-created_at",),
}

SORT_OPTIONS = (
    ("author", "Автор"),
    ("title", "Название"),
    ("year", "Год"),
    ("price", "Цена"),
    ("created_at", "Дата"),
)

DEFAULT_SORT = "author"


def _resolve_sort(sort: str) -> str:
    if sort in SORT_FIELDS:
        return sort
    return DEFAULT_SORT


def _build_sort_links(current_sort: str, request) -> list[dict]:
    links = []
    for field, label in SORT_OPTIONS:
        if current_sort == field:
            next_sort = f"-{field}"
            active = True
        elif current_sort == f"-{field}":
            next_sort = field
            active = True
        else:
            next_sort = field
            active = False

        query = request.GET.copy()
        query["sort"] = next_sort
        links.append(
            {
                "label": label,
                "url": f"?{query.urlencode()}",
                "active": active,
            }
        )
    return links


def book_list(request):
    current_sort = _resolve_sort(request.GET.get("sort", DEFAULT_SORT))
    books: QuerySet[Book] = Book.objects.all().order_by(*SORT_FIELDS[current_sort])
    context = {
        "books": books,
        "today": timezone.now(),
        "sort_links": _build_sort_links(current_sort, request),
    }
    return render(request, "books/book_list.html", context)
