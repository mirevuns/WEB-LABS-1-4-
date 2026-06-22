from decimal import Decimal

from django.core.management.base import BaseCommand

from books.models import Book


class Command(BaseCommand):
    help = "Добавляет в базу набор книг для проверки интерфейса"

    def handle(self, *args, **options):
        rows = [
            ("Мастер и Маргарита", "Михаил Булгаков", 1967, Decimal("499.00"), True),
            ("Преступление и наказание", "Фёдор Достоевский", 1866, Decimal("399.00"), True),
            ("Пикник на обочине", "Аркадий Стругацкий Борис Стругацкий", 1972, Decimal("449.50"), False),
            ("Три товарища", "Эрих Мария Ремарк", 1936, Decimal("379.00"), True),
            ("Понедельник начинается в субботу", "Аркадий Стругацкий Борис Стругацкий", 1965, Decimal("420.00"), True),
        ]

        created = 0
        for title, author, year, price, is_available in rows:
            obj, was_created = Book.objects.get_or_create(
                title=title,
                author=author,
                defaults={"year": year, "price": price, "is_available": is_available},
            )
            if not was_created:
                obj.year = year
                obj.price = price
                obj.is_available = is_available
                obj.save(update_fields=["year", "price", "is_available"])
            created += 1 if was_created else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Новых записей: {created}. Всего книг: {Book.objects.count()}"
            )
        )
