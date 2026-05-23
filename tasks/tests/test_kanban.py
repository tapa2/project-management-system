"""Тести Kanban-логіки: AJAX-зміна статусу, коментарі, права."""
from __future__ import annotations

import json

import pytest
from django.urls import reverse

from conftest import (
    CommentFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    TaskFactory,
    UserFactory,
)
from tasks.models import Comment, Task


@pytest.mark.django_db
class TestUpdateTaskStatus:
    def _url(self, task):
        return reverse('tasks:update_status', args=[task.pk])

    def _post_json(self, client, task, payload):
        return client.post(
            self._url(task),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_anonymous_redirected(self, client):
        task = TaskFactory()
        response = client.post(self._url(task), data='{}', content_type='application/json')
        assert response.status_code == 302  # @login_required → редирект на login

    def test_owner_can_move_task(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project, created_by=owner)
        client.force_login(owner)

        response = self._post_json(client, task, {'status': 'in_progress', 'order': 5})
        assert response.status_code == 200
        body = response.json()
        assert body == {
            'ok': True,
            'task': {'id': task.pk, 'status': 'in_progress', 'order': 5},
        }
        task.refresh_from_db()
        assert task.status == Task.Status.IN_PROGRESS
        assert task.order == 5

    def test_member_can_move_task(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        task = TaskFactory(project=project)
        client.force_login(member)

        response = self._post_json(client, task, {'status': 'done'})
        assert response.status_code == 200
        task.refresh_from_db()
        assert task.status == Task.Status.DONE

    def test_outsider_gets_403(self, client):
        task = TaskFactory()
        outsider = UserFactory()
        client.force_login(outsider)
        response = self._post_json(client, task, {'status': 'done'})
        assert response.status_code == 403
        assert response.json()['error'] == 'forbidden'

    def test_invalid_status_rejected(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project)
        client.force_login(owner)
        response = self._post_json(client, task, {'status': 'frozen'})
        assert response.status_code == 400
        assert response.json()['error'] == 'invalid status'

    def test_invalid_order_rejected(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project)
        client.force_login(owner)
        response = self._post_json(client, task, {'status': 'todo', 'order': 'abc'})
        assert response.status_code == 400
        assert response.json()['error'] == 'invalid order'

    def test_invalid_json_rejected(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project)
        client.force_login(owner)
        response = client.post(
            self._url(task),
            data='not-a-json',
            content_type='application/json',
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'invalid json'

    def test_get_method_not_allowed(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project)
        client.force_login(owner)
        response = client.get(self._url(task))
        assert response.status_code == 405


@pytest.mark.django_db
class TestTaskCRUD:
    def test_create_task_under_project(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        client.force_login(owner)

        response = client.post(
            reverse('tasks:create', args=[project.pk]),
            {
                'title': 'New task',
                'description': 'desc',
                'status': Task.Status.TODO,
                'priority': Task.Priority.HIGH,
                'order': 0,
            },
        )
        assert response.status_code == 302
        task = Task.objects.get(title='New task')
        assert task.project == project
        assert task.created_by == owner

    def test_outsider_cannot_create_task(self, client):
        project = ProjectFactory()
        outsider = UserFactory()
        client.force_login(outsider)
        response = client.post(
            reverse('tasks:create', args=[project.pk]),
            {'title': 'Hax', 'priority': 'medium', 'status': 'todo', 'order': 0},
        )
        assert response.status_code == 403
        assert not Task.objects.filter(title='Hax').exists()

    def test_detail_visible_to_member(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        task = TaskFactory(project=project)
        client.force_login(member)
        response = client.get(reverse('tasks:detail', args=[task.pk]))
        assert response.status_code == 200
        assert task.title.encode() in response.content

    def test_detail_blocked_for_outsider(self, client):
        task = TaskFactory()
        outsider = UserFactory()
        client.force_login(outsider)
        response = client.get(reverse('tasks:detail', args=[task.pk]))
        assert response.status_code == 403


@pytest.mark.django_db
class TestComments:
    def test_member_can_comment(self, client):
        project = ProjectFactory()
        member = UserFactory()
        ProjectMembershipFactory(project=project, user=member)
        task = TaskFactory(project=project)
        client.force_login(member)

        response = client.post(
            reverse('tasks:comment_create', args=[task.pk]),
            {'text': 'Looks good'},
        )
        assert response.status_code == 302
        assert task.comments.filter(author=member, text='Looks good').exists()

    def test_outsider_cannot_comment(self, client):
        task = TaskFactory()
        outsider = UserFactory()
        client.force_login(outsider)
        response = client.post(
            reverse('tasks:comment_create', args=[task.pk]),
            {'text': 'sneaky'},
        )
        assert response.status_code == 403
        assert not task.comments.filter(text='sneaky').exists()

    def test_empty_comment_rejected(self, client):
        owner = UserFactory()
        project = ProjectFactory(owner=owner)
        task = TaskFactory(project=project)
        client.force_login(owner)
        before = task.comments.count()
        response = client.post(
            reverse('tasks:comment_create', args=[task.pk]),
            {'text': ''},
        )
        # form_invalid → redirect, але без створення коментаря
        assert response.status_code == 302
        assert task.comments.count() == before

    def test_comment_ordering_is_chronological(self):
        task = TaskFactory()
        c1 = CommentFactory(task=task)
        c2 = CommentFactory(task=task)
        ordered = list(task.comments.all())
        assert ordered == [c1, c2]
        # str(comment) починається з представлення автора (User.__str__)
        assert str(c1).startswith(str(c1.author))
