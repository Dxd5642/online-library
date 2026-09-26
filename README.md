# LibSpace — Платформа для авторов и читателей

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

**LibSpace** 0 это современная веб-платформа для публикации и чтения книг. Проект объединяет авторов и читателей, предоставляя удобный интерфейс для создания произведений, отслеживания прогресса чтения и детальной аналитики вовлеченности аудитории.

---

## 🛠 Технологический стек

* **Backend:** Python (Django)
* **База данных:** SQLite / Django ORM
* **Frontend:** Шаблонизатор от Django

---

## ⚙️ Установка и локальный запуск 

**1. Клонирование репозитория:**
```bash
git clone [https://github.com/Dxd5642/online-library.git](https://github.com/Dxd5642/online-library.git)
cd your-repo-name
```

2. Настройка переменных окружения:
Скопируйте файл .env.example в .env и укажите необходимые параметры.
```Bash
cp .env.example .env
```

3. Применение миграций базы данных:
```Bash
python manage.py makemigrations
python manage.py migrate
```

4. Создание администратора
```Bash
python manage.py createsuperuser
```

5. Запуск проекта
```Bash
python manage.py runserver
```

После успешного запуска приложение будет доступно по адресу: http://localhost:8000 (по умолчанию).
