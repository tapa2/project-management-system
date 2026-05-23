"""Тести моделей projects.* — Project та ProjectMembership."""
from __future__ import annotations

import pytest
from django.db import IntegrityError

from conftest import ProjectFactory, ProjectMembershipFactory, UserFactory
from projects.models import Project, ProjectMembership


@pytest.mark.django_db
class TestProject:
    def test_create_project(self):
        user = UserFactory()
        project = Project.objects.create(name='Demo', owner=user)
        assert project.pk is not None
        assert project.is_active is True
        assert str(project) == 'Demo'

    def test_owner_added_to_memberships(self):
        """ProjectFactory гарантує, що owner потрапляє у membership."""
        project = ProjectFactory()
        assert project.memberships.filter(user=project.owner).exists()
        owner_ms = project.memberships.get(user=project.owner)
        assert owner_ms.role == ProjectMembership.Role.OWNER

    def test_ordering_is_recent_first(self):
        p1 = ProjectFactory()
        p2 = ProjectFactory()
        ordered = list(Project.objects.all())
        assert ordered[0] == p2
        assert ordered[1] == p1


@pytest.mark.django_db
class TestProjectMembership:
    def test_unique_per_user(self):
        project = ProjectFactory()
        outsider = UserFactory()
        ProjectMembershipFactory(project=project, user=outsider)
        with pytest.raises(IntegrityError):
            ProjectMembership.objects.create(
                project=project,
                user=outsider,
                role=ProjectMembership.Role.MANAGER,
            )

    def test_role_choices_display(self):
        project = ProjectFactory()
        ms = ProjectMembershipFactory(
            project=project,
            user=UserFactory(),
            role=ProjectMembership.Role.MANAGER,
        )
        assert ms.get_role_display() == 'Менеджер'

    def test_str_contains_project_and_user(self):
        project = ProjectFactory(name='X')
        # Очищаємо ім'я/прізвище, щоб User.__str__ повернув username
        user = UserFactory(username='alice', first_name='', last_name='')
        ms = ProjectMembershipFactory(project=project, user=user)
        assert 'X' in str(ms)
        assert 'alice' in str(ms)
