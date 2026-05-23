# Система управління проєктами

Веб-застосунок на Django для командного управління проєктами: задачі з дедлайнами, Kanban-дошка з drag-and-drop, ролі учасників, коментарі, інтеграція з Claude/Anthropic для автогенерації описів задач.

> Курсова робота на тему **«Розробка вебзастосунку «Система управління проєктами та задачами» на Django з елементами ШІ»**.

---

## Стек

| Шар | Технології |
|---|---|
| Backend | Python 3.12, Django 6.0, django-environ |
| База даних | PostgreSQL 16 |
| Брокер задач | Redis 7, Celery 5 |
| Frontend | Bootstrap 5, SortableJS (Kanban drag-and-drop), django-crispy-forms |
| ШІ | Anthropic Claude (`claude-haiku-4-5`) через офіційний SDK |
| Розгортання | Docker, docker-compose, Gunicorn, Nginx |
| Тестування | pytest, pytest-django, factory-boy, coverage |

---

## Функціональність

- **Реєстрація / автентифікація** — кастомна модель `User` з аватаркою, посадою, біо
- **Проєкти** — CRUD, власник + ManyToMany учасники через `ProjectMembership` (ролі: owner / manager / member)
- **Задачі** — статуси (todo / in_progress / review / done), пріоритети, дедлайни, виконавці, мітки, вкладення
- **Kanban-дошка** — 4 колонки за статусами, drag-and-drop між колонками з AJAX-оновленням
- **Коментарі** до задач — авторизованим учасникам проєкту
- **AI-помічник** — заголовок задачі → Claude генерує опис, чек-лист підзадач, оцінку складності у фоні (Celery → Redis), результат тягнеться AJAX-polling
- **Безпека** — CSRF, HTTPS-cookie, HSTS, X-Frame-Options DENY, перевірка прав на рівні view, секрети в `.env`
- **Адмінка** — повна підтримка всіх моделей з list_display / search_fields / list_filter

---

## Структура проєкту

```
project-management-system/
├── config/                     # settings, urls, wsgi, asgi, celery
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── accounts/                   # User, реєстрація, профіль
├── projects/                   # Project, ProjectMembership
├── tasks/                      # Task, Comment, Attachment, Label, Kanban
├── ai_assistant/               # AISuggestion, services.py (Anthropic), Celery-таск
├── core/                       # головна сторінка
├── templates/                  # глобальні шаблони (base.html, registration/)
├── static/                     # CSS/JS
├── media/                      # завантаження користувача (аватари, вкладення)
├── nginx/default.conf          # reverse proxy + статика/медіа
├── docs/                       # ER-діаграма, звіт
├── Dockerfile                  # multi-stage, python:3.12-slim
├── docker-compose.yml          # web + db + redis + celery + nginx
├── docker-compose.test.yml     # ізольований Postgres на 5433 для pytest
├── entrypoint.sh               # wait-for-db + migrate + collectstatic
├── pytest.ini                  # pytest + coverage конфіг
├── conftest.py                 # factory-boy фабрики + фікстури
├── requirements.txt
├── .env.example
└── ROADMAP.md
```

---

## Швидкий старт — Docker

Найпростіший шлях — підняти весь стек одним рядком.

```powershell
# 1. Скопіюй .env.example у .env та заповни SECRET_KEY (можна залишити дефолти DB)
Copy-Item .env.example .env

# 2. Згенеруй SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# → встав отриманий рядок у .env у DJANGO_SECRET_KEY=...

# 3. (опційно) додай ANTHROPIC_API_KEY у .env — без нього сервіс повертає mock-відповіді

# 4. Зібрати та запустити
docker compose up -d --build

# 5. Створити суперюзера
docker compose exec web python manage.py createsuperuser
```

Відкрий [http://localhost:8080](http://localhost:8080) — застосунок працює через Nginx → Gunicorn.

### Що піднімається
| Сервіс | Опис | Експонований порт |
|---|---|---|
| `nginx` | reverse-proxy, віддача `/static/`, `/media/` | `8080` (хост) |
| `web` | Django + Gunicorn (3 worker'и) | внутрішній `8000` |
| `celery` | worker для AI-генерації | — |
| `db` | PostgreSQL 16 з named volume `postgres_data` | внутрішній `5432` |
| `redis` | broker та result-backend Celery | внутрішній `6379` |

### Зупинка
```powershell
docker compose down        # зберігає дані БД
docker compose down -v     # видаляє volume з БД
```

---

## Локальний запуск (без Docker)

Знадобиться локальний PostgreSQL та Redis.

```powershell
# 1. Створи БД та юзера (один раз):
#    CREATE DATABASE pms_db;
#    CREATE USER pms_user WITH PASSWORD 'pms_password';
#    GRANT ALL PRIVILEGES ON DATABASE pms_db TO pms_user;

# 2. Virtualenv + залежності
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. .env
Copy-Item .env.example .env
# заповни DJANGO_SECRET_KEY (див. вище)

# 4. Міграції + суперюзер
python manage.py migrate
python manage.py createsuperuser

# 5. Запуск Redis локально (потрібен для Celery)
#    Або через Docker: docker run -d --name pms-redis -p 6379:6379 redis:7-alpine

# 6. В одному терміналі — Celery worker
celery -A config worker -l info -P solo   # -P solo для Windows

# 7. В іншому — Django dev-server
python manage.py runserver
```

Відкрий [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Тестування

Тести створюють власну тестову БД, тому використовуємо окремий Postgres-контейнер на порту `5433` (так пропадає необхідність давати `CREATEDB` локальному юзеру):

```powershell
# 1. Підняти ізольований Postgres для тестів
docker compose -f docker-compose.test.yml up -d

# 2. Направити pytest на нього
$env:DATABASE_URL = 'postgres://pms_user:pms_password@localhost:5433/pms_test'

# 3. Запуск
pytest

# 4. Прибрати
docker compose -f docker-compose.test.yml down -v
```

**Поточний стан:** 48 тестів проходять, coverage **96%**.

```
accounts/tests/test_auth.py        — реєстрація, login, logout, профіль
projects/tests/test_models.py      — Project, ProjectMembership, role choices
projects/tests/test_views.py       — owner vs member vs outsider, CRUD
tasks/tests/test_kanban.py         — AJAX update_status, права, коментарі
ai_assistant/tests/test_services.py — мок-режим, monkeypatch Anthropic
```

---

## Основні маршрути

| URL | View | Опис |
|---|---|---|
| `/` | `core.home` | Головна |
| `/accounts/register/` | `RegisterView` | Реєстрація |
| `/accounts/login/` | `LoginView` | Вхід |
| `/accounts/logout/` | `LogoutView` | Вихід |
| `/accounts/profile/` | `ProfileView` | Профіль |
| `/projects/` | `ProjectListView` | Список проєктів (тільки свої) |
| `/projects/new/` | `ProjectCreateView` | Створення проєкту |
| `/projects/<id>/` | `ProjectDetailView` | Сторінка проєкту + Kanban |
| `/projects/<id>/edit/` | `ProjectUpdateView` | Редагування (тільки owner) |
| `/projects/<id>/delete/` | `ProjectDeleteView` | Видалення (тільки owner) |
| `/projects/<id>/members/add/` | `AddMemberView` | Додати учасника (owner) |
| `/tasks/new/in/<project_id>/` | `TaskCreateView` | Створити задачу |
| `/tasks/<id>/` | `TaskDetailView` | Деталі + коментарі |
| `/tasks/<id>/edit/` | `TaskUpdateView` | Редагувати задачу |
| `/tasks/<id>/update-status/` | `update_task_status` | AJAX зміна статусу/порядку |
| `/tasks/<id>/comments/add/` | `CommentCreateView` | Додати коментар |
| `/ai/suggest/` | `AISuggestionRequestView` | Запит AI-опису задачі |
| `/ai/suggestions/<id>/status/` | polling | Тягнути готовий результат |
| `/admin/` | Django admin | Адмін-панель |

---

## ER-діаграма

`docs/er_diagram.dot` — `.dot` файл згенеровано через `django-extensions graph_models`. Щоб отримати PNG/SVG:

```powershell
choco install graphviz    # або: scoop install graphviz
dot -Tpng docs/er_app_models.dot -o docs/er_app_models.png
```

Текстова репрезентація (Mermaid, рендериться на GitHub):

```mermaid
erDiagram
    USER ||--o{ PROJECT : owns
    USER ||--o{ PROJECT_MEMBERSHIP : participates
    PROJECT ||--o{ PROJECT_MEMBERSHIP : has
    PROJECT ||--o{ TASK : contains
    USER ||--o{ TASK : "creates / assigned"
    TASK ||--o{ COMMENT : has
    USER ||--o{ COMMENT : writes
    TASK ||--o{ ATTACHMENT : has
    TASK }o--o{ LABEL : tagged
    USER ||--o{ AI_SUGGESTION : requests
    TASK ||--o{ AI_SUGGESTION : about

    USER {
        int id PK
        string username
        string email
        image avatar
        string position
        text bio
    }
    PROJECT {
        int id PK
        string name
        text description
        int owner_id FK
        bool is_active
        datetime created_at
    }
    PROJECT_MEMBERSHIP {
        int id PK
        int project_id FK
        int user_id FK
        string role "owner|manager|member"
        datetime joined_at
    }
    TASK {
        int id PK
        int project_id FK
        string title
        text description
        int assignee_id FK
        int created_by_id FK
        string status "todo|in_progress|review|done"
        string priority
        datetime deadline
        int order
    }
    COMMENT {
        int id PK
        int task_id FK
        int author_id FK
        text text
        datetime created_at
    }
    AI_SUGGESTION {
        int id PK
        int task_id FK
        int user_id FK
        string kind
        text prompt
        text response
    }
```

---

## Конфігурація

Усі секрети та параметри — у `.env`. Шаблон — `.env.example`. Ключові змінні:

| Змінна | Опис |
|---|---|
| `DJANGO_SECRET_KEY` | Обов'язковий, 50+ символів |
| `DJANGO_DEBUG` | `True` локально, `False` у production |
| `DJANGO_ALLOWED_HOSTS` | через кому: `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | напр. `http://localhost:8080` для Nginx-проксі |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | `redis://host:6379/0` |
| `ANTHROPIC_API_KEY` | опційно — без нього AI-сервіс повертає mock |

У production (`DEBUG=False`) автоматично вмикаються `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS=31536000`.

---

## Документація

- [`ROADMAP.md`](ROADMAP.md) — план розробки з 13 етапів
- [`docs/REPORT.md`](docs/REPORT.md) — звіт за проєктом (для експорту в PDF/DOCX)
- [`docs/er_diagram.dot`](docs/er_diagram.dot) — ER-діаграма всіх моделей
- [`docs/er_app_models.dot`](docs/er_app_models.dot) — лише наші apps (без auth/admin)

---

## Ліцензія

Навчальний проєкт, навчальне використання дозволено.
