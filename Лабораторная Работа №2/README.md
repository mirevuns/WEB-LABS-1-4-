Каталог книг (Django)

Просмотр списка на главной странице, данные в SQLite, админ‑панель для редактирования.

Запуск (Windows, PowerShell)

1) Создайте и активируйте виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\activate.bat
```

2) Установите зависимости:

```powershell
pip install -r requirements.txt
```

3) Миграции и начальные записи:

```powershell
python manage.py migrate
python manage.py seed_books
```

4) Запустите сервер:

```powershell
python manage.py runserver
```

Сайт: `http://127.0.0.1:8000/`  
Админка: `http://127.0.0.1:8000/admin/` (создайте пользователя: `python manage.py createsuperuser`)

