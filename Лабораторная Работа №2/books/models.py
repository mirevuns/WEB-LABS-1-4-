from django.db import models
from django.utils import timezone


class Book(models.Model):
    title = models.CharField("Название", max_length=200)
    author = models.CharField("Автор", max_length=120)
    year = models.PositiveIntegerField("Год издания")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Добавлено", default=timezone.now)
    is_available = models.BooleanField("В наличии", default=True)

    class Meta:
        ordering = ["author", "title"]
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self) -> str:
        return f"{self.title} — {self.author}"
