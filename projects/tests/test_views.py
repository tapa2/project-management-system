"""Тести view-ів projects — права доступу власник vs сторонній."""
from __future__ import annotations

import pytest
from django.urls import reverse

from conftest import ProjectFactory, ProjectMembershipFactory, UserFactory
from projects.models import Project, ProjectMembership


@pytest.mark.django_db
class TestProjectListView:
    def test_anonymous_redirected(self, client):
        response = client.get(reverse('projects:list'))
        assert response.status_code == 302

    def test_user_sees_only_own_or_member_projects(self, client):
        owner = UserFactory()
        outsider = UserFactory()
        mine = ProjectFactory(owner=owner, name='Mine')
        ProjectFactory(owner=outsider, name='Foreign')  # не повинен бачити

        # Сторонній проєкт, у якому owner — учасник
        shared = ProjectFactory(owner=outsider, name='Shared')
        ProjectMembershipFactory(project=shared, user=owner)

        client.force_login(owner)
        response = client.get(reverse('projects:list'))
        assert response.status_code == 200
        projects = list(response.context['projects'])
        names = {p.name for p in projects}
        assert names == {'Mine', 'Shared'}
        assert mine in projects


@pytest.mark.django_db
class TestProjectDetailAccess:
    def test_owner_can_view_detail(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        client.force_login(owner)
        response = client.get(reverse('projects:detail', args=[project.pk]))
        assert response.status_code == 200

    def test_member_can_view_detail(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        client.force_login(member)
        response = client.get(reverse('projects:detail', args=[project.pk]))
        assert response.status_code == 200

    def test_outsider_gets_404(self, client):
        project = ProjectFactory()
        outsider = UserFactory()
        client.force_login(outsider)
        response = client.get(reverse('projects:detail', args=[project.pk]))
        # ProjectAccessMixin фільтрує queryset → 404
        assert response.status_code == 404


@pytest.mark.django_db
class TestProjectCRUD:
    def test_create_project_adds_owner_membership(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse('projects:create'),
            {'name': 'Brand new', 'description': 'desc', 'is_active': 'on'},
        )
        assert response.status_code == 302
        project = Project.objects.get(name='Brand new')
        assert project.owner == user
        ms = project.memberships.get(user=user)
        assert ms.role == ProjectMembership.Role.OWNER

    def test_update_allowed_for_owner(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        client.force_login(owner)
        response = client.post(
            reverse('projects:edit', args=[project.pk]),
            {'name': 'Renamed', 'description': 'd', 'is_active': 'on'},
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == 'Renamed'

    def test_update_forbidden_for_non_owner_member(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        client.force_login(member)
        response = client.post(
            reverse('projects:edit', args=[project.pk]),
            {'name': 'Hacked', 'description': '', 'is_active': 'on'},
        )
        # ProjectOwnerRequiredMixin → 403 для UserPassesTestMixin
        assert response.status_code == 403
        project.refresh_from_db()
        assert project.name != 'Hacked'

    def test_delete_allowed_for_owner(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        client.force_login(owner)
        response = client.post(reverse('projects:delete', args=[project.pk]))
        assert response.status_code == 302
        assert not Project.objects.filter(pk=project.pk).exists()


@pytest.mark.django_db
class TestAddRemoveMember:
    def test_owner_can_add_member(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        new_member = UserFactory()
        client.force_login(owner)
        response = client.post(
            reverse('projects:add_member', args=[project.pk]),
            {'user': new_member.pk, 'role': ProjectMembership.Role.MEMBER},
        )
        assert response.status_code == 302
        assert project.memberships.filter(user=new_member).exists()

    def test_non_owner_cannot_add_member(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        client.force_login(member)
        target = UserFactory()
        response = client.post(
            reverse('projects:add_member', args=[project.pk]),
            {'user': target.pk, 'role': ProjectMembership.Role.MEMBER},
        )
        assert response.status_code == 403
        assert not project.memberships.filter(user=target).exists()
