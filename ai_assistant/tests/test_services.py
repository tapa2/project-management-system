"""Тести інтеграції з Anthropic — мокаємо клієнта, ніколи не б'ємо мережу."""
from __future__ import annotations

import pytest

from ai_assistant import services
from ai_assistant.services import generate_task_description
from ai_assistant.tasks import generate_task_description_task
from conftest import AISuggestionFactory


class _StubBlock:
    def __init__(self, text):
        self.type = 'text'
        self.text = text


class _StubMessage:
    def __init__(self, text):
        self.content = [_StubBlock(text)]


class _StubMessages:
    def __init__(self, text):
        self._text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _StubMessage(self._text)


class _StubAnthropic:
    last_instance: '_StubAnthropic | None' = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = _StubMessages('Згенерований опис задачі.')
        _StubAnthropic.last_instance = self


class _ExplodingAnthropic:
    def __init__(self, api_key):
        self.api_key = api_key

        class _M:
            def create(self_inner, **kwargs):
                raise RuntimeError('API down')

        self.messages = _M()


class TestGenerateTaskDescription:
    def test_empty_title_returns_empty(self):
        assert generate_task_description('') == ''
        assert generate_task_description('   ') == ''

    def test_mock_returned_when_no_api_key(self, settings):
        settings.ANTHROPIC_API_KEY = ''
        result = generate_task_description('Налаштувати CI')
        assert 'Налаштувати CI' in result
        assert 'mock' in result.lower()

    def test_anthropic_called_when_key_present(self, settings, monkeypatch):
        settings.ANTHROPIC_API_KEY = 'sk-test-key'
        stub_module = type('m', (), {'Anthropic': _StubAnthropic})
        monkeypatch.setitem(__import__('sys').modules, 'anthropic', stub_module)

        result = generate_task_description('Імплементувати логін')
        assert result == 'Згенерований опис задачі.'

        instance = _StubAnthropic.last_instance
        assert instance is not None
        assert instance.api_key == 'sk-test-key'
        call = instance.messages.calls[0]
        assert call['model'] == services.MODEL_ID
        assert call['system'] == services.SYSTEM_PROMPT
        assert call['messages'] == [{'role': 'user', 'content': 'Імплементувати логін'}]

    def test_falls_back_to_mock_on_api_error(self, settings, monkeypatch):
        settings.ANTHROPIC_API_KEY = 'sk-test-key'
        stub_module = type('m', (), {'Anthropic': _ExplodingAnthropic})
        monkeypatch.setitem(__import__('sys').modules, 'anthropic', stub_module)

        result = generate_task_description('Зламана задача')
        assert 'Зламана задача' in result
        assert 'API виклик не вдався' in result


@pytest.mark.django_db
class TestGenerateTaskDescriptionCeleryTask:
    def test_task_writes_response_to_suggestion(self, settings, monkeypatch):
        """Celery-таск виконується синхронно у тестах — перевіряємо, що response заповнюється."""
        settings.ANTHROPIC_API_KEY = ''  # → mock-шлях
        suggestion = AISuggestionFactory(prompt='Допиляти Kanban')

        # Викликаємо як звичайну функцію (без брокера)
        returned_pk = generate_task_description_task.run(suggestion.pk)

        assert returned_pk == suggestion.pk
        suggestion.refresh_from_db()
        assert 'Допиляти Kanban' in suggestion.response

    def test_task_records_error_and_reraises(self, monkeypatch):
        suggestion = AISuggestionFactory(prompt='будь-що')

        def boom(_title):
            raise ValueError('service exploded')

        monkeypatch.setattr('ai_assistant.tasks.generate_task_description', boom)

        with pytest.raises(ValueError):
            generate_task_description_task.run(suggestion.pk)

        suggestion.refresh_from_db()
        assert 'service exploded' in suggestion.response
