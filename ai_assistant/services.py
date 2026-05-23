"""Інтеграція з Anthropic Claude.

Якщо `ANTHROPIC_API_KEY` порожній — повертаємо детермінований mock, щоб увесь
end-to-end пайплайн (форма → Celery → AISuggestion → polling → UI) працював
без реальних викликів API. Це зручно для розробки і захисту проєкту, коли
ключ ще не активований.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ти — досвідчений тімлід. На вхід отримуєш короткий заголовок задачі. "
    "Відповідай українською у форматі Markdown:\n"
    "1. Розгорнутий опис задачі (2-4 речення).\n"
    "2. Чек-лист підзадач (markdown-списком, 3-6 пунктів).\n"
    "3. Оцінка складності (низька / середня / висока) одним рядком.\n"
    "Не додавай заголовків секцій — лише сам опис, далі список, далі рядок зі складністю."
)

MODEL_ID = 'claude-haiku-4-5-20251001'
MAX_TOKENS = 800


def _mock_response(title: str) -> str:
    return (
        f"Реалізувати задачу «{title}». Уточнити вимоги зі стейкхолдером, "
        "продумати рішення, написати код та покрити тестами.\n\n"
        "- [ ] Зібрати вимоги\n"
        "- [ ] Спроектувати рішення\n"
        "- [ ] Реалізувати функціонал\n"
        "- [ ] Написати тести\n"
        "- [ ] Code review\n\n"
        "Оцінка складності: середня\n\n"
        "_(згенеровано mock-сервісом — встанови ANTHROPIC_API_KEY у .env для реальних викликів)_"
    )


def generate_task_description(title: str) -> str:
    """Згенерувати опис задачі за заголовком. Використовує Claude або mock."""
    title = (title or '').strip()
    if not title:
        return ''

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not api_key:
        logger.info('ANTHROPIC_API_KEY not set — returning mock description for %r', title)
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
        return ''.join(block.text for block in message.content if getattr(block, 'type', None) == 'text').strip()
    except Exception:
        logger.exception('Anthropic API call failed for title=%r', title)
        return _mock_response(title) + '\n\n_(API виклик не вдався — використано mock)_'
