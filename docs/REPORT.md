# Розробка вебзастосунку «Система управління проєктами та задачами» на Django з елементами штучного інтелекту



Виконав: Тертичний Тарас, ТК32


---

## Зміст

1. [Вступ](#1-вступ)
2. [Аналіз вимог](#2-аналіз-вимог)
3. [Архітектура застосунку](#3-архітектура-застосунку)
4. [Проєктування бази даних](#4-проєктування-бази-даних)
5. [Реалізація ключових функцій](#5-реалізація-ключових-функцій)
6. [Безпека](#6-безпека)
7. [Інтеграція штучного інтелекту](#7-інтеграція-штучного-інтелекту)
8. [Розгортання](#8-розгортання)
9. [Тестування](#9-тестування)
10. [Висновки](#10-висновки)
11. [Список джерел](#11-список-джерел)
12. [Додатки](#12-додатки)

---

## 1. Вступ

### 1.1. Постановка задачі

Сучасні розподілені команди — навіть невеликі, з 3–10 учасників — стикаються з тими самими проблемами, що й великі: задачі губляться у месенджерах, дедлайни порушуються через відсутність єдиного календаря, виконавці не розуміють пріоритетів. Існують комерційні рішення (Jira, Trello, Asana), однак вони або дорогі для невеликих команд, або переускладнені, або не дають повного контролю над даними та інтеграціями.

Метою курсової роботи є проєктування та реалізація вебзастосунку, що покриває базові потреби в управлінні проєктами:

- ведення списку проєктів з ролями учасників;
- декомпозиція проєктів на задачі з дедлайнами та виконавцями;
- візуалізація прогресу через Kanban-дошку;
- комунікація через коментарі;
- автоматизація рутинних операцій за допомогою інтеграції зі штучним інтелектом.

### 1.2. Предметна область

Управління проєктами — це систематична організація робочих процесів навколо чітко визначених цілей з обмеженнями за часом, бюджетом і ресурсами. Класичним інструментом візуалізації є Kanban-дошка (від яп. «канбан» — «знак, картка»), що розділяє роботу на стани: «треба зробити», «у роботі», «на перевірці», «готово». Користувач перетягує картку через колонки, відображаючи фактичний прогрес.

### 1.3. Перелік реалізованих функцій

Система реалізує такі функції:

1. Реєстрація користувачів з підтвердженням пароля та автоматичним входом після створення облікового запису.
2. Особистий профіль з аватаром, посадою і біографією.
3. Створення, редагування та видалення проєктів (тільки власник).
4. Додавання учасників до проєкту з трьома ролями: власник, менеджер, учасник.
5. Створення задач у межах проєкту з полями: заголовок, опис, пріоритет, дедлайн, виконавець, мітки.
6. Чотириколонкова Kanban-дошка з drag-and-drop-перетягуванням карток між колонками; статус задачі оновлюється через AJAX без перезавантаження сторінки.
7. Коментарі до задач з обмеженням за правами доступу.
8. Автогенерація опису задачі через Anthropic Claude (модель `claude-haiku-4-5`) як приклад інтеграції з ШІ; виконується у фоні через Celery + Redis.
9. Адміністративна панель Django з налаштованими `list_display`, `search_fields`, `list_filter` для всіх моделей.
10. Розгортання у Docker-стек з Nginx, Gunicorn, PostgreSQL і Redis.

### 1.4. Вибір технологій

| Категорія | Обране рішення | Альтернативи | Обґрунтування |
|---|---|---|---|
| Мова | Python 3.12 | Node.js, PHP | Простота прототипування, багата екосистема ML/AI бібліотек, типізація через type hints |
| Web-фреймворк | Django 6.0 | Flask, FastAPI | MVT, вбудована адмінка, ORM, міграції, аутентифікація з коробки — мінімум boilerplate |
| СУБД | PostgreSQL 16 | MySQL, SQLite | Вимога курсової; підтримка JSONB, повноцінні constraint'и, відмінна сумісність з Django ORM |
| Брокер задач | Redis 7 + Celery 5 | RQ, APScheduler | Стандарт у Django-екосистемі; підтримка retries, monitoring, scheduling |
| Frontend-розмітка | Bootstrap 5 | Tailwind, чистий CSS | Готові компоненти, узгоджений вигляд без часу на верстку |
| Drag-and-drop | SortableJS | jQuery UI, react-dnd | Працює без React, мала вага (~6 КБ), підтримує всі бажані події |
| Шаблонізатор | Django Templates + crispy-forms | Jinja2 | Стандарт; crispy дає швидку Bootstrap-розмітку форм |
| ШІ-провайдер | Anthropic Claude (Haiku 4.5) | OpenAI GPT, Gemini | Швидка модель, низька ціна, добре працює з українською; офіційний Python SDK |
| Розгортання | Docker + Nginx + Gunicorn | uwsgi, runserver | Стандарт індустрії; одна команда — повноцінне середовище |

---

## 2. Аналіз вимог

### 2.1. Функціональні вимоги

| № | Вимога | Реалізація |
|---|---|---|
| F1 | Реєстрація з валідацією пароля та email | `accounts/forms.py` — `UserRegistrationForm` на базі `UserCreationForm` |
| F2 | Вхід / вихід з системи | `accounts/urls.py` — стандартні `auth_views.LoginView`, `LogoutView` |
| F3 | Перегляд та редагування власного профілю | `accounts/views.py` — `ProfileView`, `ProfileUpdateView` |
| F4 | Створення / редагування / видалення проєктів | `projects/views.py` — `ProjectCreateView`, `ProjectUpdateView`, `ProjectDeleteView` |
| F5 | Список проєктів фільтрується за участю | `ProjectAccessMixin.get_queryset()` — `Q(owner=user) \| Q(members=user)` |
| F6 | Додавання та видалення учасників | `AddMemberView`, `RemoveMemberView` — обмежено `test_func` до власника |
| F7 | Створення / редагування задач у проєкті | `tasks/views.py` — `TaskCreateView`, `TaskUpdateView` |
| F8 | Зміна статусу задачі через drag-and-drop | `tasks/views.py:update_task_status` — AJAX endpoint |
| F9 | Коментарі до задач | `CommentCreateView` |
| F10 | Автогенерація опису задачі через ШІ | `ai_assistant/views.py:request_description` → Celery |

### 2.2. Нефункціональні вимоги

- **Безпека.** CSRF на всіх формах, secure-cookie в production, HSTS, X-Frame-Options DENY, перевірка прав на рівні view, ORM (без raw SQL) → захист від SQL-ін'єкцій, секрети поза репозиторієм.
- **Продуктивність.** Запити `select_related` / `prefetch_related` у view-ах списків; pagination 12 проєктів на сторінку; AJAX замість повного перезавантаження.
- **Розгортання.** Один `docker compose up -d --build` піднімає весь стек з нуля. Stateless web-контейнер — можна горизонтально масштабувати.
- **Підтримуваність.** Поділ на 5 застосунків за зонами відповідальності; покриття тестами 96%; типізація сигнатур функцій; коментарі тільки там, де "чому".
- **Інтернаціоналізація.** `LANGUAGE_CODE='uk'`, `USE_TZ=True`, `TIME_ZONE='Europe/Kyiv'`. Усі verbose_name та повідомлення — українською.

### 2.3. Ролі користувачів

| Роль | Можливості |
|---|---|
| **Анонімний** | Доступ лише до сторінок `/`, `/accounts/login/`, `/accounts/register/`. Інші сторінки редиректять на login. |
| **Зареєстрований** | Створювати власні проєкти; бачити проєкти, де він власник або учасник; коментувати задачі. |
| **Власник проєкту** | Усе вище + редагувати/видаляти проєкт, додавати/видаляти учасників, повноцінно керувати задачами. |
| **Учасник (member)** | Бачити проєкт, створювати/змінювати задачі, перетягувати їх на Kanban, коментувати. Не може видаляти проєкт чи керувати учасниками. |
| **Адміністратор Django** | Повний доступ через `/admin/` — для технічного супроводу. |

### 2.4. User stories

1. *Як зареєстрований користувач, я хочу створити проєкт і запросити колег, щоб ми могли разом вести задачі.*
2. *Як власник проєкту, я хочу додати задачу одним кліком, маючи лише заголовок, щоб ШІ автоматично запропонував детальний опис і чек-лист.*
3. *Як учасник, я хочу перетягувати картку через колонки Kanban, щоб команда одразу бачила прогрес.*
4. *Як виконавець, я хочу залишати коментарі під задачами, щоб обговорювати деталі поруч із самою задачею, а не у месенджері.*
5. *Як власник, я хочу бачити, які задачі прострочені, щоб реагувати на ризики дедлайну.*

---

## 3. Архітектура застосунку

### 3.1. Загальна схема

Застосунок дотримується класичної архітектури **MVT** (Model–View–Template), яку пропонує Django:

```
            ┌────────────┐
   HTTP →   │   Nginx    │  ← статика /static/, /media/
            └─────┬──────┘
                  ▼
            ┌────────────┐
            │  Gunicorn  │  ← WSGI, 3 worker'и
            └─────┬──────┘
                  ▼
            ┌────────────┐      ┌─────────┐
            │   Django   │ ←──→ │PostgreSQL│
            │  (config)  │      └─────────┘
            └─────┬──────┘      
                  │ delay()      ┌─────────┐
                  ├────────────→ │  Redis  │  ← broker
                  │              └────┬────┘
                  ▼                   ▼
            ┌────────────┐      ┌──────────┐
            │   Browser  │      │  Celery  │ → Anthropic API
            └────────────┘      └──────────┘
```

### 3.2. Поділ на застосунки (apps)

| App | Відповідальність |
|---|---|
| `config` | settings, urls, wsgi, asgi, celery.py |
| `accounts` | кастомна модель `User`, реєстрація, профіль, групи |
| `projects` | моделі `Project`, `ProjectMembership`; CRUD; права доступу |
| `tasks` | моделі `Task`, `Comment`, `Attachment`, `Label`; Kanban; AJAX-статус |
| `ai_assistant` | модель `AISuggestion`, інтеграція з Anthropic, Celery-таски |
| `core` | головна сторінка, базові шаблони |

Поділ на apps відповідає принципу **single responsibility**: кожен app — це самодостатній модуль з власними моделями, view-ами, шаблонами та URL-ами. Це спрощує переиспользування і паралельну розробку.

### 3.3. Конфігураційні файли

- **`config/settings.py`** — єдина точка конфігурації. Усі значення зчитуються з `.env` через `django-environ`.
- **`config/urls.py`** — головний роутер, вмикає `accounts/`, `projects/`, `tasks/`, `ai/` та `admin/`.
- **`config/celery.py`** — створює `Celery('config')` і викликає `autodiscover_tasks()`, який автоматично знаходить `tasks.py` у всіх застосунках:

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

- **`.env`** — секрети та параметри середовища (не комітиться).
- **`.env.example`** — шаблон з усіма змінними та коментарями.
- **`requirements.txt`** — заморожений список залежностей через `pip freeze`.
- **`pytest.ini`** — конфіг тестового раннера з `--reuse-db` і `--cov` для всіх apps.

### 3.4. Структура директорій

```
project-management-system/
├── config/                # settings, urls, wsgi, celery
├── accounts/              # User + auth views
├── projects/              # Project + memberships
├── tasks/                 # Task + Kanban + Comment
├── ai_assistant/          # Claude integration + Celery
├── core/                  # home page
├── templates/             # base.html + registration/
├── static/                # CSS / JS
├── media/                 # завантаження користувачів
├── nginx/                 # default.conf для reverse proxy
├── docs/                  # ER-діаграма, звіт
├── Dockerfile             # multi-stage build
├── docker-compose.yml     # web + db + redis + celery + nginx
├── entrypoint.sh          # wait-for-db + migrate + collectstatic
└── manage.py
```

---

## 4. Проєктування бази даних

### 4.1. ER-діаграма

ER-діаграма згенерована автоматично через `django-extensions graph_models -a -o docs/er_diagram.dot`. Текстова репрезентація у форматі Mermaid (рендериться на GitHub):

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
```

### 4.2. Перелік моделей та їх полів

#### accounts.User

Кастомна модель, що успадковує `AbstractUser`. Додано три поля для профілю:

```python
class User(AbstractUser):
    avatar   = models.ImageField(upload_to='avatars/', blank=True, null=True)
    position = models.CharField(max_length=120, blank=True)
    bio      = models.TextField(blank=True)
```

#### projects.Project

```python
class Project(models.Model):
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    owner       = models.ForeignKey(User, on_delete=CASCADE, related_name='owned_projects')
    members     = models.ManyToManyField(User, through='ProjectMembership',
                                         related_name='projects')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_active   = models.BooleanField(default=True)
```

#### projects.ProjectMembership (through-модель)

```python
class ProjectMembership(models.Model):
    class Role(TextChoices):
        OWNER   = 'owner',   'Власник'
        MANAGER = 'manager', 'Менеджер'
        MEMBER  = 'member',  'Учасник'

    project   = ForeignKey(Project, on_delete=CASCADE, related_name='memberships')
    user      = ForeignKey(User,    on_delete=CASCADE, related_name='memberships')
    role      = CharField(choices=Role.choices, default=Role.MEMBER)
    joined_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
```

#### tasks.Task

```python
class Task(models.Model):
    class Status(TextChoices):
        TODO = 'todo'; IN_PROGRESS = 'in_progress'
        REVIEW = 'review'; DONE = 'done'
    class Priority(TextChoices):
        LOW = 'low'; MEDIUM = 'medium'
        HIGH = 'high'; CRITICAL = 'critical'

    project     = ForeignKey('projects.Project', on_delete=CASCADE, related_name='tasks')
    title       = CharField(max_length=200)
    description = TextField(blank=True)
    assignee    = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True,
                             related_name='assigned_tasks')
    created_by  = ForeignKey(User, on_delete=SET_NULL, null=True,
                             related_name='created_tasks')
    status      = CharField(choices=Status.choices, default=Status.TODO)
    priority    = CharField(choices=Priority.choices, default=Priority.MEDIUM)
    deadline    = DateTimeField(null=True, blank=True)
    labels      = ManyToManyField('Label', blank=True, related_name='tasks')
    order       = PositiveIntegerField(default=0)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)
```

Поле `order` додано спеціально для Kanban: дозволяє зберігати позицію всередині колонки після перетягування.

#### tasks.Comment, Attachment, Label

```python
class Comment(models.Model):
    task       = ForeignKey(Task, on_delete=CASCADE, related_name='comments')
    author     = ForeignKey(User, on_delete=CASCADE, related_name='comments')
    text       = TextField()
    created_at = DateTimeField(auto_now_add=True)

class Attachment(models.Model):
    task        = ForeignKey(Task, on_delete=CASCADE, related_name='attachments')
    file        = FileField(upload_to='attachments/%Y/%m/')
    uploaded_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    uploaded_at = DateTimeField(auto_now_add=True)

class Label(models.Model):
    name  = CharField(max_length=40, unique=True)
    color = CharField(max_length=7, default='#6c757d')   # HEX
```

#### ai_assistant.AISuggestion

```python
class AISuggestion(models.Model):
    class Kind(TextChoices):
        DESCRIPTION = 'description'; CATEGORIZATION = 'categorization'
        CHAT = 'chat'; OTHER = 'other'

    task       = ForeignKey('tasks.Task', on_delete=SET_NULL, null=True, blank=True,
                            related_name='ai_suggestions')
    user       = ForeignKey(User, on_delete=CASCADE, related_name='ai_suggestions')
    kind       = CharField(choices=Kind.choices, default=Kind.OTHER)
    prompt     = TextField()
    response   = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
```

### 4.3. Типи зв'язків

| Зв'язок | Тип |
|---|---|
| User → Project (owner) | One-to-Many (FK) |
| User ↔ Project (members) | Many-to-Many через `ProjectMembership` |
| Project → Task | One-to-Many |
| User → Task (assignee, created_by) | One-to-Many (два окремі FK з різними related_name) |
| Task → Comment | One-to-Many |
| Task → Attachment | One-to-Many |
| Task ↔ Label | Many-to-Many |
| User → AISuggestion | One-to-Many |
| Task → AISuggestion | One-to-Many (nullable — generic-запити без прив'язки до задачі) |

### 4.4. Міграції

Усі моделі створено через Django-міграції:

- `accounts/0001_initial.py` — кастомна модель `User`.
- `accounts/0002_create_groups.py` — **data migration**: створює групи `Manager` та `Developer`:

```python
def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ['Manager', 'Developer']:
        Group.objects.get_or_create(name=name)
```

- `projects/0001_initial.py` — Project + ProjectMembership.
- `tasks/0001_initial.py` — Task + Comment + Attachment + Label.
- `ai_assistant/0001_initial.py` — AISuggestion.

Міграції зберігаються у репозиторії — це гарантує однакову схему у всіх розробників і на проді.

---

## 5. Реалізація ключових функцій

### 5.1. Аутентифікація та права доступу

Кастомна модель `User` зафіксована в `settings.AUTH_USER_MODEL = 'accounts.User'`. Реєстрація використовує `UserCreationForm` з доданими полями email, first_name, last_name:

```python
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name  = forms.CharField(max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password1', 'password2')
```

`RegisterView` після успіху одразу логінить користувача:

```python
class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
```

Усі view-и, що потребують аутентифікації, наслідують `LoginRequiredMixin` (CBV) або декорум `@login_required` (FBV). Перевірка прав на доступ до конкретного проєкту реалізована через `UserPassesTestMixin`:

```python
class ProjectOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        project = self.get_object()
        return project.owner_id == self.request.user.id
```

### 5.2. CRUD проєктів з фільтрацією за участю

Ключова деталь — `ProjectListView` показує лише ті проєкти, де користувач є власником **або** учасником. Запит:

```python
class ProjectAccessMixin(LoginRequiredMixin):
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()
```

При створенні проєкту автоматично додається `ProjectMembership` з роллю `OWNER`:

```python
def form_valid(self, form):
    form.instance.owner = self.request.user
    response = super().form_valid(form)
    ProjectMembership.objects.create(
        project=self.object,
        user=self.request.user,
        role=ProjectMembership.Role.OWNER,
    )
    return response
```

### 5.3. Kanban-дошка з drag-and-drop

На сторінці `ProjectDetailView` шаблон рендерить 4 колонки за статусами:

```python
ctx['kanban_columns'] = [
    {
        'status': value,
        'label': label,
        'tasks': [t for t in tasks if t.status == value],
    }
    for value, label in Task.Status.choices
]
```

Front-end використовує SortableJS — підключена з CDN бібліотека для drag-and-drop. Кожна колонка — `<div class="kanban-column" data-status="todo">...</div>`. JavaScript ініціалізує `Sortable(...)` з обробником `onAdd`/`onUpdate`, який надсилає AJAX-запит:

```javascript
fetch(`/tasks/${taskId}/update-status/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ status: newStatus, order: newOrder }),
});
```

Серверна частина (`tasks/views.py`):

```python
@login_required
@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task.objects.select_related('project'), pk=pk)
    if not _user_has_project_access(request.user, task.project):
        return JsonResponse({'error': 'forbidden'}, status=403)

    payload = json.loads(request.body or '{}')
    new_status = payload.get('status')
    valid_statuses = {choice[0] for choice in Task.Status.choices}
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'invalid status'}, status=400)

    task.status = new_status
    if 'order' in payload:
        task.order = int(payload['order'])
    with transaction.atomic():
        task.save(update_fields=['status', 'order', 'updated_at'])

    return JsonResponse({'ok': True, ...})
```

Декоратори `@login_required` + `@require_POST` гарантують аутентифікацію та обмеження методу. CSRF-токен надходить у заголовку — Django валідує його стандартним middleware.

### 5.4. Коментарі

`CommentCreateView` приймає лише POST. Перевіряє доступ до проєкту через ту саму функцію `_user_has_project_access`:

```python
class CommentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = CommentForm
    http_method_names = ['post']

    def test_func(self):
        return _user_has_project_access(self.request.user, self.task.project)

    def form_valid(self, form):
        form.instance.task = self.task
        form.instance.author = self.request.user
        form.save()
        return redirect('tasks:detail', pk=self.task.pk)
```

---

## 6. Безпека

Заходи безпеки реалізовано у `config/settings.py`:

```python
# Завжди:
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# Тільки коли DEBUG=False (production):
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000          # 1 рік
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
```

| Загроза | Захист |
|---|---|
| **CSRF** | `CsrfViewMiddleware`, `{% csrf_token %}` у всіх формах, `X-CSRFToken` у AJAX-заголовку |
| **XSS** | Auto-escaping Django Templates за замовчуванням; `\|safe` ніде не використовується для користувацького вводу |
| **SQL-ін'єкція** | Виключно через ORM, без `.raw()` / `cursor.execute()` з конкатенацією |
| **Clickjacking** | `X_FRAME_OPTIONS = 'DENY'` |
| **Man-in-the-middle** | `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `HSTS` 1 рік + preload |
| **Bruteforce реєстрації** | `AUTH_PASSWORD_VALIDATORS` (мін. довжина, не схожий на username, не з common-листа, не лише цифри) |
| **Виток секретів** | `SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY` — лише з `.env`; `.env` у `.gitignore` |
| **Несанкціонований доступ до даних** | `LoginRequiredMixin`/`@login_required`; `UserPassesTestMixin` для рівня запису; queryset-фільтрація за `owner`/`members` |

Запуск перевірки `python manage.py check --deploy` у production-режимі (`DEBUG=False`) проходить без помилок.

---

## 7. Інтеграція штучного інтелекту

### 7.1. Обраний сценарій

З трьох варіантів, наведених у ROADMAP (А — автогенерація опису, Б — категоризація, В — чат-помічник), реалізовано **варіант А** — автогенерація детального опису задачі за коротким заголовком. Це найприродніший сценарій для початку роботи з задачею: користувач вводить «Налаштувати CI/CD», а ШІ генерує опис, чек-лист підзадач і оцінку складності.

### 7.2. Послідовність взаємодії

```
Браузер             Django View               Celery Worker             Anthropic API
    │                    │                          │                          │
    │── POST /ai/suggest/ {title}                   │                          │
    │                    │                          │                          │
    │                    ├── create AISuggestion(prompt=title, response='')    │
    │                    │                          │                          │
    │                    ├── generate_task_description_task.delay(id)          │
    │                    │                          │                          │
    │ ←── 200 {id, pending}                         │                          │
    │                    │                          │                          │
    │                    │                          ├── client.messages.create │
    │                    │                          │ ←── текст відповіді ─────┤
    │                    │                          │                          │
    │                    │                          ├── suggestion.response = ...│
    │                    │                          ├── suggestion.save()      │
    │                    │                          │                          │
    │── GET  /ai/suggestions/<id>/status/ ───────────                          │
    │                    │                          │                          │
    │ ←── 200 {ready, response} ──                  │                          │
```

### 7.3. Реалізація

**`ai_assistant/services.py`** — функція виклику Anthropic SDK з graceful-fallback на mock, якщо ключа немає або API недоступний:

```python
MODEL_ID = 'claude-haiku-4-5-20251001'
MAX_TOKENS = 800
SYSTEM_PROMPT = (
    "Ти — досвідчений тімлід. На вхід отримуєш короткий заголовок задачі. "
    "Відповідай українською у форматі Markdown:\n"
    "1. Розгорнутий опис задачі (2-4 речення).\n"
    "2. Чек-лист підзадач (markdown-списком, 3-6 пунктів).\n"
    "3. Оцінка складності одним рядком."
)

def generate_task_description(title: str) -> str:
    title = (title or '').strip()
    if not title:
        return ''
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not api_key:
        return _mock_response(title)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': title}],
        )
        return ''.join(b.text for b in message.content if b.type == 'text').strip()
    except Exception:
        logger.exception('Anthropic API call failed')
        return _mock_response(title) + '\n\n_(API виклик не вдався — використано mock)_'
```

**`ai_assistant/tasks.py`** — Celery-таск:

```python
@shared_task(bind=True, name='ai_assistant.generate_task_description')
def generate_task_description_task(self, suggestion_id: int) -> int:
    suggestion = AISuggestion.objects.get(pk=suggestion_id)
    try:
        suggestion.response = generate_task_description(suggestion.prompt)
    except Exception as exc:
        suggestion.response = f'Помилка генерації: {exc}'
        suggestion.save(update_fields=['response'])
        raise
    suggestion.save(update_fields=['response'])
    return suggestion.pk
```

**`ai_assistant/views.py`** — два endpoint-и: `request_description` створює `AISuggestion` і викликає `task.delay(...)`, `suggestion_status` — polling.

### 7.4. Безпека ключа

`ANTHROPIC_API_KEY` зчитується лише з `.env`:

```python
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
```

`.env` у `.gitignore`. У репозиторії — лише `.env.example` з порожнім значенням і коментарем «Заповни тільки той, який реально використовуєш».

Це означає, що клонувати репозиторій і запустити можна без ключа — система працюватиме у mock-режимі. 

---

## 8. Розгортання

### 8.1. Dockerfile

Multi-stage build на основі `python:3.12-slim`. Перша стадія (builder) збирає wheel-и з усіма системними залежностями (build-essential, libpq-dev, libjpeg-dev). Друга стадія (runtime) встановлює лише runtime-бібліотеки (libpq5, libjpeg62-turbo) і пакети з готових wheel-ів — це зменшує фінальний образ:

```dockerfile
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libjpeg-dev zlib1g-dev
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
RUN apt-get install -y --no-install-recommends libpq5 libjpeg62-turbo netcat-openbsd
RUN groupadd --system django && useradd --system --gid django --home /app django
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels -r requirements.txt
COPY . .
USER django
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

Запуск під непривілейованим користувачем `django` — захист від escalation у разі компрометації застосунку.

### 8.2. docker-compose.yml

П'ять сервісів:

| Сервіс | Образ | Призначення |
|---|---|---|
| `db` | `postgres:16-alpine` | Основна БД. Дані у named volume `postgres_data`. |
| `redis` | `redis:7-alpine` | Broker і result-backend для Celery. |
| `web` | власний `pms-web:latest` | Django + Gunicorn. Healthcheck на db/redis. |
| `celery` | той самий `pms-web:latest` | `celery -A config worker -l info`. |
| `nginx` | `nginx:1.27-alpine` | Reverse-proxy на `web:8000`. Експонує порт `8080` хоста. |

Named volumes:
- `postgres_data` — щоб БД переживала перезапуск контейнера;
- `static_volume` — `web` запускає `collectstatic` у нього, `nginx` віддає звідти;
- `media_volume` — спільне сховище завантажень користувачів.

### 8.3. entrypoint.sh

Стартовий скрипт чекає на готовність БД через `netcat`, виконує `migrate` і `collectstatic` (якщо ввімкнено env-флагом), і передає управління `CMD`:

```bash
for i in {1..60}; do
    if nc -z "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"; then break; fi
    sleep 1
done

if [[ "${RUN_MIGRATIONS:-0}" == "1" ]]; then
    python manage.py migrate --noinput
fi
if [[ "${RUN_COLLECTSTATIC:-0}" == "1" ]]; then
    python manage.py collectstatic --noinput
fi
exec "$@"
```

Celery-контейнер запускається з `RUN_MIGRATIONS=0` — щоб не намагатися робити міграції паралельно з web-контейнером.

### 8.4. Nginx

`nginx/default.conf`:

```nginx
upstream django { server web:8000; }

server {
    listen 80;
    client_max_body_size 20M;

    location /static/ { alias /app/staticfiles/; expires 30d; }
    location /media/  { alias /app/media/;       expires 7d;  }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Nginx бере на себе віддачу статики й вкладень, розвантажуючи Python-процеси.

### 8.5. Послідовність запуску

```powershell
cp .env.example .env             # заповнити DJANGO_SECRET_KEY
docker compose up -d --build     # збір образу + старт усіх 5 сервісів
docker compose exec web python manage.py createsuperuser
# Готово — http://localhost:8080
```

---

## 9. Тестування

### 9.1. Інструментарій

- **pytest 9** — основний раннер.
- **pytest-django** — інтеграція з Django (database fixtures, settings).
- **pytest-cov** — звіт по покриттю.
- **factory-boy 3** — генерація тестових об'єктів.
- **Faker** — реалістичні випадкові дані.

### 9.2. Конфігурація

**`pytest.ini`:**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
addopts =
    -ra --strict-markers --reuse-db
    --cov=accounts --cov=projects --cov=tasks --cov=ai_assistant
    --cov-report=term-missing
testpaths = accounts projects tasks ai_assistant
```

**Окремий Postgres для тестів** — `docker-compose.test.yml` піднімає інстанс на порту 5433. Це дозволяє не давати `CREATEDB` локальному юзеру `pms_user`:

```yaml
services:
  test-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: pms_test
      POSTGRES_USER: pms_user
      POSTGRES_PASSWORD: pms_password
    ports: ["5433:5432"]
    tmpfs: ["/var/lib/postgresql/data"]
```

`tmpfs` означає, що дані тестової БД зберігаються лише в оперативній пам'яті — тести бігають швидше і не лишають слідів.

### 9.3. Фабрики

**`conftest.py`** містить factory-boy фабрики для всіх моделей. Приклад для `Project`:

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f'Project {n}')
    description = factory.Faker('sentence')
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def with_owner_membership(self, create, extracted, **kwargs):
        if not create:
            return
        ProjectMembership.objects.get_or_create(
            project=self, user=self.owner,
            defaults={'role': ProjectMembership.Role.OWNER},
        )
```

Це гарантує, що кожен створений проєкт автоматично має owner-membership — інакше тести access-mixin'а були б непослідовні.

### 9.4. Перелік тестів

**`accounts/tests/test_auth.py`** (9 тестів):
- Реєстрація: GET форми, POST успіх з автологіном, відхилення pwd-mismatch.
- Логін: успіх, відхилення невірного пароля.
- Logout: видалення сесії.
- Профіль: редирект анонімного, доступ авторизованого, оновлення.

**`projects/tests/test_models.py`** (6 тестів):
- Створення Project, str(), порядок сортування за датою.
- ProjectMembership: unique-constraint, role choices display, str().

**`projects/tests/test_views.py`** (12 тестів):
- Список фільтрується (свої проєкти + ті, де користувач — учасник).
- Detail: owner, member — 200; outsider — 404.
- Edit/Delete: лише власник; member отримує 403.
- AddMember: лише власник.

**`tasks/tests/test_kanban.py`** (15 тестів):
- AJAX `update_task_status`: owner/member — 200; outsider — 403; invalid status/order/JSON — 400; GET — 405.
- TaskCreateView: під проєктом owner-а — 302; outsider — 403.
- TaskDetail: member — 200; outsider — 403.
- Comments: member може, outsider — 403, empty — відхилено.

**`ai_assistant/tests/test_services.py`** (6 тестів):
- Empty title → пустий рядок.
- Без API-ключа → mock-відповідь, що містить заголовок.
- З ключем — monkeypatch SDK, перевірка переданих параметрів (model, system, messages).
- Помилка API → fallback на mock з позначкою.
- Celery-таск пише response; ловить помилку і записує її, потім re-raise.

### 9.5. Запуск та результат

```powershell
docker compose -f docker-compose.test.yml up -d
$env:DATABASE_URL = 'postgres://pms_user:pms_password@localhost:5433/pms_test'
pytest
```

Результат:

```
============================= test session starts =============================
collected 48 items

accounts/tests/test_auth.py .........            [ 18%]
ai_assistant/tests/test_services.py ......       [ 31%]
projects/tests/test_models.py ......             [ 43%]
projects/tests/test_views.py ............        [ 68%]
tasks/tests/test_kanban.py ...............       [100%]

TOTAL coverage: 96%

============================= 48 passed in 31s =============================
```

Покриття **96%** — вище за вимогу 60% з ROADMAP.

---

## 10. Висновки

У межах курсової роботи спроєктовано та реалізовано повноцінний вебзастосунок для управління проєктами та задачами з елементами штучного інтелекту.

**Виконано:**

1. Реалізовано всі функціональні вимоги: реєстрація, ролі, CRUD проєктів і задач, Kanban з drag-and-drop, коментарі, ШІ-генерація опису через Anthropic Claude.
2. Дотримано принципів MVT, з чітким поділом застосунку на 5 апів за зонами відповідальності.
3. Спроєктовано реляційну модель даних з 8 сутностями, FK, M2M (через through-модель) і data-міграцією для груп.
4. Інтегровано асинхронну обробку через Celery + Redis — ШІ-запити не блокують HTTP-відповідь.
5. Налаштовано production-secured deploy через Docker + Nginx + Gunicorn з multi-stage збіркою.
6. Покрито код тестами на 96%, з ізольованим тестовим Postgres у Docker.

**Особисті враження.**

Django довів свою силу як платформа для швидкого MVP: ORM, адмінка, форми, міграції, аутентифікація — все «з коробки» працює без боку, а коли треба змінити поведінку — кожна частина має чіткі hook'и розширення (`Mixin`-и, `clean`-методи форм, `form_valid`).

Інтеграція з Anthropic SDK виявилася найпростішою частиною: 30 рядків коду в `services.py`, ще 10 — для Celery-обгортки. Складніше було продумати UX навколо «фоновий запит → polling → відображення».

Найбільше часу зайняла Docker-частина: правильна послідовність layer-ів для кешу, healthcheck-залежності між сервісами, ізольований Postgres для тестів. Але результат — `docker compose up -d --build` піднімає повноцінне production-середовище за 2 хвилини на чистій машині.

**Що можна покращити надалі:**

1. Real-time оновлення Kanban через WebSocket (Django Channels) замість AJAX-polling для статусу AI-задач.
2. Розширення ШІ-сценаріїв — Варіанти Б (категоризація) і В (чат-помічник) з ROADMAP.
3. API-шар (DRF) для мобільного клієнта.
4. CI/CD pipeline на GitHub Actions з автоматичним тестуванням і деплоєм.
5. Можливість прикріплювати файли до коментарів (зараз тільки до задач).

---

## 11. Список джерел

1. Django Software Foundation. *Django 6.0 documentation*. URL: https://docs.djangoproject.com/en/6.0/
2. Django Software Foundation. *Customizing authentication in Django*. URL: https://docs.djangoproject.com/en/6.0/topics/auth/customizing/
3. Celery Project. *Celery — Distributed Task Queue (5.x)*. URL: https://docs.celeryq.dev/en/stable/
4. Anthropic. *Anthropic Python SDK*. URL: https://github.com/anthropics/anthropic-sdk-python
5. Anthropic. *Claude models overview*. URL: https://docs.anthropic.com/claude/docs/models-overview
6. PostgreSQL Global Development Group. *PostgreSQL 16 documentation*. URL: https://www.postgresql.org/docs/16/
7. Redis Ltd. *Redis 7 documentation*. URL: https://redis.io/docs/
8. NGINX, Inc. *NGINX configuration reference*. URL: https://nginx.org/en/docs/
9. pytest-dev. *pytest documentation*. URL: https://docs.pytest.org/en/stable/
10. pytest-dev. *pytest-django plugin*. URL: https://pytest-django.readthedocs.io/
11. factory-boy contributors. *factory_boy documentation*. URL: https://factoryboy.readthedocs.io/
12. SortableJS. *SortableJS — JavaScript library for reorderable drag-and-drop lists*. URL: https://sortablejs.github.io/Sortable/
13. Bootstrap Team. *Bootstrap 5 documentation*. URL: https://getbootstrap.com/docs/5.3/
14. Docker Inc. *Docker documentation*. URL: https://docs.docker.com/
15. Joachim Jablon. *django-environ — Django-friendly handling of environment variables*. URL: https://django-environ.readthedocs.io/
16. OWASP Foundation. *OWASP Top 10 — 2021*. URL: https://owasp.org/Top10/

---

## 12. Додатки

### Додаток А. Посилання на репозиторій

Публічний GitHub-репозиторій з повним кодом, історією комітів, тестами та документацією:

**https://github.com/tapa2/project-management-system**

### Додаток Б. ER-діаграма

Файл `docs/er_diagram.dot` (повна схема з службовими auth-моделями) та `docs/er_app_models.dot` (лише власні apps). Згенеровано командою:

```powershell
python manage.py graph_models accounts projects tasks ai_assistant --dot -o docs/er_app_models.dot
```

Для рендерингу у PNG/SVG треба встановити Graphviz і виконати:

```powershell
dot -Tpng docs/er_app_models.dot -o docs/er_app_models.png
```

### Додаток В. Шаблон `.env.example`

```dotenv
DJANGO_SECRET_KEY=change-me-to-a-50-char-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

DATABASE_URL=postgres://pms_user:pms_password@localhost:5432/pms_db
POSTGRES_DB=pms_db
POSTGRES_USER=pms_user
POSTGRES_PASSWORD=pms_password

REDIS_URL=redis://localhost:6379/0

ANTHROPIC_API_KEY=
OPENAI_API_KEY=

NGINX_PORT=8080
```

### Додаток Г. Історія розробки (git log, скорочено)

```
a3a9c24 test: tasks and kanban tests
7acb3fe test: auth and projects tests
505d7f8 feat: nginx config and static collection
e5fc05a feat: dockerfile and docker-compose
264eb9a feat: production security settings
fd4ed26 feat: anthropic ai integration for task description
6898a5f feat: celery + redis integration
004f9c0 feat: kanban board with drag-and-drop
e1f0e41 feat: task CRUD and comments
302f346 feat: project CRUD views with access control
0b57993 feat: registration, login, logout, profile with bootstrap templates
58a7204 feat: tasks models with comments and ai_assistant scaffolding
1dbe5cd feat: projects models and admin
7400da4 feat: accounts app with custom user model
e5f8aed feat: env-based settings, postgres config
4b49d2a feat: django project skeleton with apps
a37cf14 chore: initial commit
```

Кожен коміт відповідає одному завершеному кроку з ROADMAP — це дозволяє відстежити логіку розробки лінійно.

### Додаток Д. Карта URL-маршрутів

| URL | View | Метод | Доступ |
|---|---|---|---|
| `/` | `core.home` | GET | Усі |
| `/accounts/register/` | `RegisterView` | GET, POST | Анонімний |
| `/accounts/login/` | `LoginView` | GET, POST | Анонімний |
| `/accounts/logout/` | `LogoutView` | POST | Авториз. |
| `/accounts/profile/` | `ProfileView` | GET | Авториз. |
| `/accounts/profile/edit/` | `ProfileUpdateView` | GET, POST | Авториз. |
| `/projects/` | `ProjectListView` | GET | Учасники |
| `/projects/new/` | `ProjectCreateView` | GET, POST | Авториз. |
| `/projects/<id>/` | `ProjectDetailView` | GET | Учасники |
| `/projects/<id>/edit/` | `ProjectUpdateView` | GET, POST | Власник |
| `/projects/<id>/delete/` | `ProjectDeleteView` | GET, POST | Власник |
| `/projects/<id>/members/add/` | `AddMemberView` | GET, POST | Власник |
| `/projects/members/<id>/remove/` | `RemoveMemberView` | POST | Власник |
| `/tasks/new/in/<project_id>/` | `TaskCreateView` | GET, POST | Учасники |
| `/tasks/<id>/` | `TaskDetailView` | GET | Учасники |
| `/tasks/<id>/edit/` | `TaskUpdateView` | GET, POST | Учасники |
| `/tasks/<id>/delete/` | `TaskDeleteView` | GET, POST | Учасники |
| `/tasks/<id>/comments/add/` | `CommentCreateView` | POST | Учасники |
| `/tasks/<id>/update-status/` | `update_task_status` | POST (AJAX) | Учасники |
| `/ai/suggest/` | `request_description` | POST (AJAX) | Авториз. |
| `/ai/suggestions/<id>/status/` | `suggestion_status` | GET (AJAX) | Власник запиту |
| `/admin/` | Django admin | — | is_staff |

---

*Кінець звіту.*
