(function () {
    'use strict';

    function getCookie(name) {
        const m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
        return m ? decodeURIComponent(m[1]) : null;
    }

    function setStatus(el, text, kind) {
        el.className = 'small mt-1 text-' + (kind || 'muted');
        el.textContent = text;
    }

    function pollSuggestion(statusUrl, attempt, ctx) {
        const MAX_ATTEMPTS = 30;
        const DELAY = 1000;
        if (attempt >= MAX_ATTEMPTS) {
            setStatus(ctx.statusEl, 'Таймаут очікування відповіді. Спробуй ще раз.', 'danger');
            ctx.btn.disabled = false;
            return;
        }
        fetch(statusUrl, {credentials: 'same-origin', headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.status === 'ready') {
                    ctx.target.value = data.response;
                    ctx.target.dispatchEvent(new Event('input', {bubbles: true}));
                    setStatus(ctx.statusEl, '✔ Опис згенеровано. Можеш редагувати перед збереженням.', 'success');
                    ctx.btn.disabled = false;
                } else {
                    setStatus(ctx.statusEl, 'Генерується… (' + (attempt + 1) + '/' + MAX_ATTEMPTS + ')', 'muted');
                    setTimeout(function () { pollSuggestion(statusUrl, attempt + 1, ctx); }, DELAY);
                }
            })
            .catch(function (err) {
                console.error(err);
                setStatus(ctx.statusEl, 'Помилка polling: ' + err, 'danger');
                ctx.btn.disabled = false;
            });
    }

    function init() {
        const btn = document.getElementById('ai-generate-btn');
        if (!btn) { return; }
        const titleField = document.getElementById('id_title');
        const descField  = document.getElementById('id_description');
        const statusEl   = document.getElementById('ai-status');
        if (!titleField || !descField || !statusEl) { return; }

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const title = (titleField.value || '').trim();
            if (!title) {
                setStatus(statusEl, 'Введи спочатку заголовок задачі.', 'warning');
                titleField.focus();
                return;
            }
            btn.disabled = true;
            setStatus(statusEl, 'Надсилаю запит…', 'muted');

            fetch(btn.dataset.requestUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({title: title}),
            })
                .then(function (r) {
                    if (!r.ok) { throw new Error('HTTP ' + r.status); }
                    return r.json();
                })
                .then(function (data) {
                    const statusUrl = btn.dataset.statusUrlTemplate.replace('0', data.suggestion_id);
                    setStatus(statusEl, 'Генерується…', 'muted');
                    pollSuggestion(statusUrl, 0, {btn: btn, target: descField, statusEl: statusEl});
                })
                .catch(function (err) {
                    console.error(err);
                    setStatus(statusEl, 'Не вдалося надіслати запит: ' + err, 'danger');
                    btn.disabled = false;
                });
        });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
