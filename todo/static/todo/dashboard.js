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

    // Update task counts in UI from JSON data
    const updateTaskCounts = (data) => {
        if (!data) return;

        // Update group chips in toolbar
        if (data.groups) {
            data.groups.forEach((group) => {
                const chip = document.querySelector(`[data-group-chip="${group.id}"]`);
                if (chip) {
                    const small = chip.querySelector('small');
                    if (small) {
                        small.textContent = `${group.task_count} zadań`;
                    }
                }
            });
        }

        // Update inbox count
        if (data.inbox_count !== undefined) {
            const inboxChip = document.querySelector('[data-group-chip="inbox"]');
            if (inboxChip) {
                const small = inboxChip.querySelector('small');
                if (small) {
                    small.textContent = `${data.inbox_count} zadań`;
                }
            }
        }
    };

    // Enhanced drag and drop
    const initDragAndDrop = () => {
        const cards = document.querySelectorAll('.task-card');
        const columns = document.querySelectorAll('.board-column');
        let draggedCard = null;
        let dragOverColumn = null;
        let placeholder = null;

        const createPlaceholder = () => {
            const ph = document.createElement('div');
            ph.className = 'task-card-placeholder';
            ph.style.height = '80px';
            ph.style.border = '2px dashed var(--accent)';
            ph.style.borderRadius = 'var(--radius-lg)';
            ph.style.background = 'rgba(92, 124, 250, 0.08)';
            ph.style.margin = '8px 0';
            return ph;
        };

        const setColumnHoverState = (column, isHovering) => {
            if (!column) return;
            column.classList.toggle('is-target', isHovering);
            const columnBody = column.querySelector('[data-column-list]');
            if (columnBody) {
                columnBody.classList.toggle('is-over', isHovering);
            }
        };

        const resetColumnHoverStates = () => {
            columns.forEach((column) => setColumnHoverState(column, false));
            if (placeholder && placeholder.parentNode) {
                placeholder.parentNode.removeChild(placeholder);
            }
            placeholder = null;
            dragOverColumn = null;
        };

        const getDragAfterElement = (container, y) => {
            const elements = [...container.querySelectorAll('.task-card:not(.is-dragging):not(.task-card-placeholder)')];
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
            const formData = new FormData();
            formData.append('group_id', groupId ?? '');
            formData.append('position', position ?? 0);
            formData.append('csrfmiddlewaretoken', csrfToken);

            fetch(`/task/${taskId}/move/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Accept': 'application/json',
                },
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        updateTaskCounts(data);
                    }
                })
                .catch((error) => {
                    console.error('Nie udało się przenieść zadania', error);
                    // Reload page on error
                    window.location.reload();
                });
        };

        cards.forEach((card) => {
            card.addEventListener('dragstart', (e) => {
                draggedCard = card;
                card.classList.add('is-dragging');
                // Store original group ID before moving
                card.dataset.originalGroupId = card.dataset.groupId || '';
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', card.outerHTML);
                // Create a ghost image
                const dragImage = card.cloneNode(true);
                dragImage.style.opacity = '0.5';
                document.body.appendChild(dragImage);
                dragImage.style.position = 'absolute';
                dragImage.style.top = '-1000px';
                e.dataTransfer.setDragImage(dragImage, 0, 0);
                setTimeout(() => document.body.removeChild(dragImage), 0);
            });

            card.addEventListener('dragend', () => {
                if (!draggedCard) return;
                draggedCard.classList.remove('is-dragging');
                resetColumnHoverStates();
                draggedCard = null;
            });
        });

        columns.forEach((column) => {
            const columnBody = column.querySelector('[data-column-list]');
            if (!columnBody) return;

            columnBody.addEventListener('dragenter', (event) => {
                event.preventDefault();
                if (!draggedCard) return;
                dragOverColumn = column;
                setColumnHoverState(column, true);
            });

            columnBody.addEventListener('dragover', (event) => {
                event.preventDefault();
                event.dataTransfer.dropEffect = 'move';
                if (!draggedCard) return;

                const afterElement = getDragAfterElement(columnBody, event.clientY);

                // Remove old placeholder
                if (placeholder && placeholder.parentNode) {
                    placeholder.parentNode.removeChild(placeholder);
                }

                // Insert placeholder
                if (!placeholder) {
                    placeholder = createPlaceholder();
                }

                if (afterElement == null) {
                    columnBody.appendChild(placeholder);
                } else {
                    columnBody.insertBefore(placeholder, afterElement);
                }
            });

            columnBody.addEventListener('dragleave', (event) => {
                if (!columnBody.contains(event.relatedTarget)) {
                    setColumnHoverState(column, false);
                    if (placeholder && placeholder.parentNode) {
                        placeholder.parentNode.removeChild(placeholder);
                    }
                    placeholder = null;
                    dragOverColumn = null;
                }
            });

            columnBody.addEventListener('drop', (event) => {
                event.preventDefault();
                if (!draggedCard) return;

                const taskId = draggedCard.dataset.taskId;
                const groupId = column.dataset.groupId || '';
                const siblings = [...columnBody.querySelectorAll('.task-card:not(.is-dragging):not(.task-card-placeholder)')];

                // Remove placeholder
                if (placeholder && placeholder.parentNode) {
                    placeholder.parentNode.removeChild(placeholder);
                }
                placeholder = null;

                // Insert card at correct position
                const afterElement = getDragAfterElement(columnBody, event.clientY);
                if (afterElement == null) {
                    columnBody.appendChild(draggedCard);
                } else {
                    columnBody.insertBefore(draggedCard, afterElement);
                }

                const position = siblings.indexOf(draggedCard) + 1;
                draggedCard.dataset.groupId = groupId;

                setColumnHoverState(column, false);
                dragOverColumn = null;

                // Update counts immediately
                const chip = column.querySelector('.column-actions .chip');
                if (chip) {
                    const newCount = columnBody.querySelectorAll('.task-card:not(.task-card-placeholder)').length;
                    chip.textContent = newCount;
                }

                // Update source column count (use original group ID)
                const originalGroupId = draggedCard.dataset.originalGroupId || '';
                if (originalGroupId && originalGroupId !== groupId) {
                    const sourceColumn = document.querySelector(`[data-group-id="${originalGroupId}"]`);
                    if (sourceColumn && sourceColumn !== column) {
                        const sourceBody = sourceColumn.querySelector('[data-column-list]');
                        if (sourceBody) {
                            const sourceChip = sourceColumn.querySelector('.column-actions .chip');
                            if (sourceChip) {
                                const sourceCount = sourceBody.querySelectorAll('.task-card:not(.task-card-placeholder)').length;
                                sourceChip.textContent = sourceCount;
                            }
                        }
                    }
                } else if (!originalGroupId && groupId) {
                    // Moving from inbox to a group
                    const inboxColumn = document.querySelector('[data-group-id=""]');
                    if (inboxColumn) {
                        const inboxBody = inboxColumn.querySelector('[data-column-list]');
                        if (inboxBody) {
                            const inboxChip = inboxColumn.querySelector('.column-actions .chip');
                            if (inboxChip) {
                                const inboxCount = inboxBody.querySelectorAll('.task-card:not(.task-card-placeholder)').length;
                                inboxChip.textContent = inboxCount;
                            }
                        }
                    }
                } else if (originalGroupId && !groupId) {
                    // Moving from a group to inbox
                    const sourceColumn = document.querySelector(`[data-group-id="${originalGroupId}"]`);
                    if (sourceColumn) {
                        const sourceBody = sourceColumn.querySelector('[data-column-list]');
                        if (sourceBody) {
                            const sourceChip = sourceColumn.querySelector('.column-actions .chip');
                            if (sourceChip) {
                                const sourceCount = sourceBody.querySelectorAll('.task-card:not(.task-card-placeholder)').length;
                                sourceChip.textContent = sourceCount;
                            }
                        }
                    }
                }

                // Send request to server
                moveTaskRequest(taskId, groupId, position);
            });
        });
    };

    // Group filter form - auto-submit on change
    const groupFilterForm = document.querySelector('.group-filter-form');
    if (groupFilterForm) {
        const checkboxes = groupFilterForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', () => {
                // If "Wszystkie" is checked, uncheck others
                if (checkbox.name === 'view_all' && checkbox.checked) {
                    checkboxes.forEach((cb) => {
                        if (cb !== checkbox) {
                            cb.checked = false;
                        }
                    });
                } else if (checkbox.name !== 'view_all') {
                    // If any other is checked, uncheck "Wszystkie"
                    const viewAll = groupFilterForm.querySelector('input[name="view_all"]');
                    if (viewAll) {
                        viewAll.checked = false;
                    }
                }
                // Auto-submit after a short delay
                clearTimeout(groupFilterForm._submitTimeout);
                groupFilterForm._submitTimeout = setTimeout(() => {
                    groupFilterForm.submit();
                }, 300);
            });
        });
    }

    window.addEventListener('DOMContentLoaded', () => {
        initDragAndDrop();
    });
})();
