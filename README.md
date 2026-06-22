# WEB-LABS-1-4

Лабораторные работы по курсу Web.

## Содержание

- `Лабораторная Работа №1` — клиент-сервер на сокетах
- `Лабораторная Работа №2` — Django: каталог книг, шаблоны и теги
- `Лабораторная Работа №3+4` — Django: модели магазина, админка, корзины

## Запуск Django-проектов

```bash
cd "Лабораторная Работа №2"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Аналогично для `Лабораторная Работа №3+4`.
