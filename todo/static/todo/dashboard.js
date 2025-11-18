(() => {
    const doc = document.documentElement;
    const body = document.body;
    const themeToggle = document.querySelector('[data-theme-toggle]');
    const storedTheme = localStorage.getItem('fomo-theme') || 'dark';

    const applyTheme = (mode) => {
        doc.setAttribute('data-theme', mode);
        localStorage.setItem('fomo-theme', mode);
        if (themeToggle) {
            themeToggle.querySelector('.theme-toggle__icon').textContent = mode === 'dark' ? '🌙' : '☀️';
        }
    };

    applyTheme(storedTheme);

    themeToggle?.addEventListener('click', () => {
        const current = doc.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(current);
    });

    let activeModal = null;

    const openModal = (modalId) => {
        const modal = document.querySelector(`[data-modal="${modalId}"]`);
        if (!modal) return;
        if (activeModal && activeModal !== modal) {
            closeActiveModal();
        }
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        body.classList.add('modal-open');
        activeModal = modal;
    };

    const closeActiveModal = () => {
        if (!activeModal) return;
        activeModal.classList.remove('is-open');
        activeModal.setAttribute('aria-hidden', 'true');
        activeModal = null;
        body.classList.remove('modal-open');
    };

    document.querySelectorAll('[data-open-modal]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-open-modal');
            openModal(targetId);
        });
    });

    document.querySelectorAll('[data-close-modal]').forEach((el) => {
        el.addEventListener('click', closeActiveModal);
    });

    doc.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeActiveModal();
            document.querySelectorAll('[data-dropdown]').forEach((dropdown) => dropdown.classList.remove('is-open'));
        }
    });

    // Dropdown filters
    const dropdowns = document.querySelectorAll('[data-dropdown]');

    const closeAllDropdowns = () => {
        dropdowns.forEach((dropdown) => dropdown.classList.remove('is-open'));
    };

    document.querySelectorAll('[data-toggle-dropdown]').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const container = btn.closest('[data-dropdown]');
            if (!container) return;
            const isOpen = container.classList.toggle('is-open');
            dropdowns.forEach((dropdown) => {
                if (dropdown !== container) {
                    dropdown.classList.remove('is-open');
                }
            });
            if (!isOpen) {
                container.classList.remove('is-open');
            }
        });
    });

    document.addEventListener('click', (event) => {
        if (!event.target.closest('[data-dropdown]')) {
            closeAllDropdowns();
        }
    });

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const queryString = body.dataset.queryString ? `?${body.dataset.queryString}` : '';

    const getDragAfterElement = (container, y) => {
        const elements = [...container.querySelectorAll('.task-card:not(.is-dragging)')];
        return elements.reduce(
            (closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                if (offset < 0 && offset > closest.offset) {
                    return { offset, element: child };
                }
                return closest;
            },
            { offset: Number.NEGATIVE_INFINITY, element: null },
        ).element;
    };

    const moveTaskRequest = (taskId, groupId, position) => {
        const url = `/task/${taskId}/move/${queryString}`;
        const formData = new FormData();
        formData.append('group_id', groupId ?? '');
        formData.append('position', position ?? 0);
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData,
        }).catch((error) => {
            console.error('Nie udało się przenieść zadania', error);
        });
    };

    const initDragAndDrop = () => {
        const cards = document.querySelectorAll('.task-card');
        const columns = document.querySelectorAll('.board-column');
        let draggedCard = null;

        cards.forEach((card) => {
            card.addEventListener('dragstart', () => {
                draggedCard = card;
                card.classList.add('is-dragging');
            });
            card.addEventListener('dragend', () => {
                if (!draggedCard) return;
                draggedCard.classList.remove('is-dragging');
                draggedCard = null;
            });
        });

        columns.forEach((column) => {
            const columnBody = column.querySelector('[data-column-list]');
            if (!columnBody) return;

            columnBody.addEventListener('dragover', (event) => {
                event.preventDefault();
                if (!draggedCard) return;
                const afterElement = getDragAfterElement(columnBody, event.clientY);
                if (afterElement == null) {
                    columnBody.appendChild(draggedCard);
                } else {
                    columnBody.insertBefore(draggedCard, afterElement);
                }
            });

            columnBody.addEventListener('drop', () => {
                if (!draggedCard) return;
                const taskId = draggedCard.dataset.taskId;
                const groupId = column.dataset.groupId || '';
                const siblings = [...columnBody.querySelectorAll('.task-card')];
                const position = siblings.indexOf(draggedCard) + 1;
                draggedCard.dataset.groupId = groupId;
                moveTaskRequest(taskId, groupId, position);
            });
        });
    };

    window.addEventListener('DOMContentLoaded', initDragAndDrop);
})();

