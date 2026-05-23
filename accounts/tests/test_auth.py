"""Тести реєстрації, входу, виходу та доступу до профілю."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestRegistration:
    url = reverse('accounts:register')

    def test_get_register_page(self, client):
        response = client.get(self.url)
        assert response.status_code == 200
        assert b'<form' in response.content

    def test_register_creates_user_and_logs_in(self, client):
        payload = {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'first_name': 'New',
            'last_name': 'Bie',
            'password1': 'StrongPass!234',
            'password2': 'StrongPass!234',
        }
        response = client.post(self.url, payload)
        assert response.status_code == 302
        assert User.objects.filter(username='newbie').exists()
        # Після реєстрації користувач має бути залогінений
        assert client.session['_auth_user_id']

    def test_register_rejects_password_mismatch(self, client):
        response = client.post(
            self.url,
            {
                'username': 'bad',
                'email': 'bad@example.com',
                'password1': 'StrongPass!234',
                'password2': 'OtherPass!234',
            },
        )
        assert response.status_code == 200
        assert not User.objects.filter(username='bad').exists()


@pytest.mark.django_db
class TestLoginLogout:
    def test_login_with_valid_credentials(self, client, user):
        url = reverse('accounts:login')
        response = client.post(
            url,
            {'username': user.username, 'password': 'pass12345!'},
        )
        assert response.status_code == 302
        assert client.session['_auth_user_id'] == str(user.pk)

    def test_login_rejects_bad_password(self, client, user):
        response = client.post(
            reverse('accounts:login'),
            {'username': user.username, 'password': 'wrong'},
        )
        assert response.status_code == 200
        assert '_auth_user_id' not in client.session

    def test_logout(self, auth_client):
        response = auth_client.post(reverse('accounts:logout'))
        # Після виходу — редирект
        assert response.status_code in (302, 200)
        assert '_auth_user_id' not in auth_client.session


@pytest.mark.django_db
class TestProfileAccess:
    def test_anonymous_redirected_to_login(self, client):
        url = reverse('accounts:profile')
        response = client.get(url)
        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_authenticated_sees_profile(self, auth_client, user):
        response = auth_client.get(reverse('accounts:profile'))
        assert response.status_code == 200
        assert user.username.encode() in response.content

    def test_profile_update(self, auth_client, user):
        response = auth_client.post(
            reverse('accounts:profile_edit'),
            {
                'first_name': 'Updated',
                'last_name': user.last_name,
                'email': user.email,
                'position': 'QA Lead',
                'bio': 'updated bio',
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.position == 'QA Lead'
