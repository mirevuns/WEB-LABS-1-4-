from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Название")),
                ("author", models.CharField(max_length=120, verbose_name="Автор")),
                ("year", models.PositiveIntegerField(verbose_name="Год издания")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Добавлено")),
                ("is_available", models.BooleanField(default=True, verbose_name="В наличии")),
            ],
            options={
                "verbose_name": "Книга",
                "verbose_name_plural": "Книги",
                "ordering": ["author", "title"],
            },
        ),
    ]

