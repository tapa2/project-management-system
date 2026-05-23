(function () {
    'use strict';

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[1]) : null;
    }

    function postStatus(url, status, order) {
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({status: status, order: order}),
        });
    }

    function flash(card, ok) {
        card.style.transition = 'background-color 0.4s';
        card.style.backgroundColor = ok ? '#d1e7dd' : '#f8d7da';
        setTimeout(function () {
            card.style.backgroundColor = '';
        }, 600);
    }

    function attach(column) {
        new Sortable(column, {
            group: 'kanban',
            animation: 150,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: function (evt) {
                const card = evt.item;
                const newStatus = evt.to.dataset.status;
                const newOrder = evt.newIndex;
                const url = card.dataset.updateUrl;
                if (!url) { return; }

                postStatus(url, newStatus, newOrder)
                    .then(function (r) {
                        if (!r.ok) { throw new Error('HTTP ' + r.status); }
                        return r.json();
                    })
                    .then(function () { flash(card, true); })
                    .catch(function (err) {
                        console.error('Kanban update failed:', err);
                        flash(card, false);
                        evt.from.insertBefore(card, evt.from.children[evt.oldIndex]);
                    });
            },
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.kanban-list').forEach(attach);
    });
})();
