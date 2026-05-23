"""Глобальні pytest-фікстури та factory-boy-фабрики для всього проєкту.

DB для тестів: береться зі змінної оточення DATABASE_URL. За замовчуванням
це локальний Postgres з .env. Щоб ганяти тести на ізольованому Postgres з
docker-compose.test.yml — задай DATABASE_URL перед запуском:

    $env:DATABASE_URL='postgres://pms_user:pms_password@localhost:5433/pms_test'
    pytest

django-environ не перезаписує вже встановлені OS-змінні, тому таке
задання вигравaє над тим, що лежить у .env.
"""
from __future__ import annotations

import factory
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from ai_assistant.models import AISuggestion
from projects.models import Project, ProjectMembership
from tasks.models import Comment, Task


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'pass12345!')


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f'Project {n}')
    description = factory.Faker('sentence')
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def with_owner_membership(self, create, extracted, **kwargs):
        """Власник автоматично додається у memberships з роллю owner."""
        if not create:
            return
        ProjectMembership.objects.get_or_create(
            project=self,
            user=self.owner,
            defaults={'role': ProjectMembership.Role.OWNER},
        )


class ProjectMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectMembership
        django_get_or_create = ('project', 'user')

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = ProjectMembership.Role.MEMBER


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('paragraph')
    created_by = factory.SelfAttribute('project.owner')
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SelfAttribute('task.project.owner')
    text = factory.Faker('sentence')


class AISuggestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AISuggestion

    user = factory.SubFactory(UserFactory)
    kind = AISuggestion.Kind.DESCRIPTION
    prompt = factory.Faker('sentence')
    response = ''


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def project_factory():
    return ProjectFactory


@pytest.fixture
def task_factory():
    return TaskFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def project(db, user):
    return ProjectFactory(owner=user)


@pytest.fixture
def task(db, project):
    return TaskFactory(project=project, created_by=project.owner)


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def now():
    return timezone.now()
