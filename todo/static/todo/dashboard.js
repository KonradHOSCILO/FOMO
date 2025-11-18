(() => {
    'use strict';

    // Task Form Submission
    const taskForm = document.querySelector('[data-task-form]');
    const taskTitleInput = document.querySelector('[data-task-title-input]');
    const taskDescriptionInput = document.querySelector('[data-task-description-input]');

    if (taskForm && taskTitleInput) {
        taskForm.addEventListener('submit', (e) => {
            const title = taskTitleInput.value.trim();
            if (!title) {
                e.preventDefault();
                return;
            }

            // Get description and set hidden field
            const description = taskDescriptionInput ? taskDescriptionInput.value.trim() : '';
            const hiddenDescriptionField = document.getElementById('id_task_description');
            if (hiddenDescriptionField) {
                hiddenDescriptionField.value = description;
            }

            // Get selected repeat frequency and set hidden field
            const selectedRepeat = taskForm.querySelector('input[name="repeat_frequency"]:checked');
            if (selectedRepeat) {
                const hiddenRepeat = document.getElementById('id_task_repeat_frequency');
                if (hiddenRepeat) {
                    hiddenRepeat.value = selectedRepeat.value;
                }
            }

            // Get selected group and set hidden field
            const hiddenGroupField = document.getElementById('id_task_group');
            if (hiddenGroupField) {
                // Value is already set by the group selector
            }

            // Don't prevent default - let the form submit normally
            // This ensures proper form submission with all fields
        });

        // Also submit on Enter key (but not in description)
        taskTitleInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                // Trigger form submission
                taskForm.requestSubmit();
            }
        });
    }

    // Group Selector Dropdown (in task input)
    // This is independent from the sidebar group filter - it only affects new task creation
    const groupSelectorBtn = document.querySelector('[data-toggle-group-dropdown]');
    const groupSelectorDropdown = document.querySelector('[data-group-selector-dropdown]');
    const selectedGroupName = document.querySelector('[data-selected-group-name]');
    const hiddenGroupField = document.getElementById('id_task_group');

    // Initialize group selector - always starts with "Brak" (no group)
    // This is independent from the sidebar filter
    if (hiddenGroupField) {
        hiddenGroupField.value = '';
    }

    if (groupSelectorBtn && groupSelectorDropdown) {
        groupSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            groupSelectorDropdown.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!groupSelectorDropdown.contains(e.target) && !groupSelectorBtn.contains(e.target)) {
                groupSelectorDropdown.classList.remove('open');
            }
        });

        // Handle group selection
        const groupOptions = groupSelectorDropdown.querySelectorAll('.group-selector-option');
        groupOptions.forEach((option) => {
            option.addEventListener('click', () => {
                const groupId = option.dataset.groupId || '';
                const groupName = option.dataset.groupName;

                // Update hidden field (always exists, just update value)
                if (hiddenGroupField) {
                    hiddenGroupField.value = groupId;
                } else {
                    // Create hidden field if it doesn't exist
                    const newField = document.createElement('input');
                    newField.type = 'hidden';
                    newField.name = 'task-group';
                    newField.id = 'id_task_group';
                    newField.value = groupId;
                    taskForm.appendChild(newField);
                }

                // Update displayed name
                if (selectedGroupName) {
                    selectedGroupName.textContent = groupName;
                }

                // Close dropdown
                groupSelectorDropdown.classList.remove('open');
            });
        });
    }

    // Group Selection (sidebar)
    const groupButtons = document.querySelectorAll('.sidebar-group-btn[data-group-id]');
    groupButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const groupId = btn.dataset.groupId;
            if (groupId) {
                const currentUrl = new URL(window.location);
                currentUrl.searchParams.set('group', groupId);
                window.location.href = currentUrl.toString();
            }
        });
    });

    // Group Menu (3-dot button) Dropdown
    const groupMenuButtons = document.querySelectorAll('[data-toggle-group-menu]');
    groupMenuButtons.forEach((btn) => {
        const groupId = btn.dataset.toggleGroupMenu;
        const menu = document.querySelector(`[data-group-menu="${groupId}"]`);
        
        if (menu) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Close all other menus
                document.querySelectorAll('.group-menu-dropdown').forEach((m) => {
                    if (m !== menu) {
                        m.classList.remove('open');
                    }
                });
                menu.classList.toggle('open');
            });
        }
    });

    // Close group menus when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.group-menu-btn') && !e.target.closest('.group-menu-dropdown')) {
            document.querySelectorAll('.group-menu-dropdown').forEach((menu) => {
                menu.classList.remove('open');
            });
        }
    });

    // Group Color Editing
    const editGroupButtons = document.querySelectorAll('[data-edit-group]');
    editGroupButtons.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const groupId = btn.dataset.editGroup;
            // Create a color picker
            const colorInput = document.createElement('input');
            colorInput.type = 'color';
            colorInput.value = '#0078d4'; // Default color
            colorInput.style.position = 'absolute';
            colorInput.style.opacity = '0';
            colorInput.style.width = '1px';
            colorInput.style.height = '1px';
            
            colorInput.addEventListener('change', (e) => {
                const newColor = e.target.value;
                // Submit color update via form
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/group/${groupId}/edit/`;
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
                const colorField = document.createElement('input');
                colorField.type = 'hidden';
                colorField.name = 'color';
                colorField.value = newColor;
                form.appendChild(colorField);
                document.body.appendChild(form);
                form.submit();
            });
            
            document.body.appendChild(colorInput);
            colorInput.click();
            setTimeout(() => document.body.removeChild(colorInput), 100);
        });
    });

    // Modal Handling
    const modals = document.querySelectorAll('[data-modal]');
    const openGroupFormBtn = document.querySelector('[data-open-group-form]');
    const groupModal = document.querySelector('[data-modal="group-modal"]');
    const closeModalButtons = document.querySelectorAll('[data-close-modal]');

    if (openGroupFormBtn && groupModal) {
        openGroupFormBtn.addEventListener('click', () => {
            groupModal.setAttribute('aria-hidden', 'false');
        });
    }

    // Close modal function
    const closeModal = (modal) => {
        if (modal) {
            modal.setAttribute('aria-hidden', 'true');
            // If it's the task edit modal, remove it from DOM
            if (modal.dataset.modal === 'task-edit-modal') {
                const container = document.getElementById('task-edit-modal-container');
                if (container) {
                    container.innerHTML = '';
                }
            }
        }
    };

    closeModalButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('[data-modal]') || document.querySelector('[data-modal]');
            closeModal(modal);
        });
    });

    // Close modal on backdrop click (using event delegation for dynamically added modals)
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-backdrop')) {
            const modal = e.target.closest('[data-modal]');
            closeModal(modal);
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            modals.forEach((modal) => {
                closeModal(modal);
            });
            // Also close dropdowns
            document.querySelectorAll('.group-selector-dropdown, .group-menu-dropdown').forEach((dropdown) => {
                dropdown.classList.remove('open');
            });
        }
    });

    // Task Edit Modal
    const editTaskButtons = document.querySelectorAll('[data-edit-task]');
    const taskEditContainer = document.getElementById('task-edit-modal-container');
    
    editTaskButtons.forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const taskId = btn.dataset.editTask;
            
            // Load form via AJAX
            try {
                const response = await fetch(`/task/${taskId}/edit/`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                const html = await response.text();
                
                // Insert modal HTML
                if (taskEditContainer) {
                    taskEditContainer.innerHTML = html;
                    
                    // Show modal
                    const modal = taskEditContainer.querySelector('[data-modal="task-edit-modal"]');
                    if (modal) {
                        modal.setAttribute('aria-hidden', 'false');
                        
                        // Handle form submission
                        const form = modal.querySelector('form');
                        if (form) {
                            form.addEventListener('submit', async (e) => {
                                e.preventDefault();
                                const formData = new FormData(form);
                                
                                try {
                                    const submitResponse = await fetch(form.action, {
                                        method: 'POST',
                                        body: formData,
                                        headers: {
                                            'X-Requested-With': 'XMLHttpRequest',
                                        },
                                    });
                                    
                                    if (submitResponse.ok) {
                                        const result = await submitResponse.json();
                                        if (result.success) {
                                            // Reload page to show updated task
                                            window.location.reload();
                                        }
                                    }
                                } catch (err) {
                                    console.error('Error submitting form:', err);
                                    // Fallback to regular form submission
                                    form.submit();
                                }
                            });
                            
                            // Re-attach close button handlers for dynamically added modal
                            modal.querySelectorAll('[data-close-modal]').forEach((btn) => {
                                btn.addEventListener('click', () => {
                                    closeModal(modal);
                                });
                            });
                        }
                    }
                }
            } catch (err) {
                console.error('Error loading edit form:', err);
                // Fallback to navigation
                window.location.href = `/task/${taskId}/edit/`;
            }
        });
    });

    // Task Drag and Drop
    const taskList = document.querySelector('[data-task-list]');
    if (taskList) {
        let draggedTask = null;
        let draggedOverTask = null;

        taskList.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('task-item') || e.target.closest('.task-item')) {
                draggedTask = e.target.classList.contains('task-item') ? e.target : e.target.closest('.task-item');
                draggedTask.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }
        });

        taskList.addEventListener('dragend', (e) => {
            if (draggedTask) {
                draggedTask.classList.remove('dragging');
                draggedTask = null;
                draggedOverTask = null;
            }
        });

        taskList.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            const taskItem = e.target.closest('.task-item');
            if (taskItem && taskItem !== draggedTask) {
                draggedOverTask = taskItem;
                const rect = taskItem.getBoundingClientRect();
                const midpoint = rect.top + rect.height / 2;
                
                if (e.clientY < midpoint) {
                    taskItem.classList.add('drag-over-top');
                    taskItem.classList.remove('drag-over-bottom');
                } else {
                    taskItem.classList.add('drag-over-bottom');
                    taskItem.classList.remove('drag-over-top');
                }
            }
        });

        taskList.addEventListener('dragleave', (e) => {
            const taskItem = e.target.closest('.task-item');
            if (taskItem) {
                taskItem.classList.remove('drag-over-top', 'drag-over-bottom');
            }
        });

        taskList.addEventListener('drop', (e) => {
            e.preventDefault();
            const targetTask = e.target.closest('.task-item');
            
            if (draggedTask && targetTask && draggedTask !== targetTask) {
                const rect = targetTask.getBoundingClientRect();
                const midpoint = rect.top + rect.height / 2;
                const insertBefore = e.clientY < midpoint;
                
                // Get new position
                const tasks = Array.from(taskList.querySelectorAll('.task-item'));
                const targetIndex = tasks.indexOf(targetTask);
                const newPosition = insertBefore ? targetIndex : targetIndex + 1;
                
                // Move in DOM
                if (insertBefore) {
                    taskList.insertBefore(draggedTask, targetTask);
                } else {
                    taskList.insertBefore(draggedTask, targetTask.nextSibling);
                }
                
                // Update position in database
                const taskId = draggedTask.dataset.taskId;
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                
                fetch(`/task/${taskId}/reorder/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    },
                    body: `position=${newPosition}`,
                }).catch(err => {
                    console.error('Error reordering task:', err);
                    // Reload page on error
                    window.location.reload();
                });
            }
            
            // Clean up
            taskList.querySelectorAll('.task-item').forEach(item => {
                item.classList.remove('drag-over-top', 'drag-over-bottom');
            });
        });
    }

    // Group Drag and Drop
    const groupList = document.querySelector('[data-group-list]');
    if (groupList) {
        let draggedGroup = null;
        let draggedOverGroup = null;

        groupList.addEventListener('dragstart', (e) => {
            const groupWrapper = e.target.closest('.sidebar-group-wrapper');
            if (groupWrapper) {
                draggedGroup = groupWrapper;
                draggedGroup.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }
        });

        groupList.addEventListener('dragend', (e) => {
            if (draggedGroup) {
                draggedGroup.classList.remove('dragging');
                draggedGroup = null;
                draggedOverGroup = null;
            }
        });

        groupList.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            const groupWrapper = e.target.closest('.sidebar-group-wrapper');
            if (groupWrapper && groupWrapper !== draggedGroup) {
                draggedOverGroup = groupWrapper;
                const rect = groupWrapper.getBoundingClientRect();
                const midpoint = rect.top + rect.height / 2;
                
                if (e.clientY < midpoint) {
                    groupWrapper.classList.add('drag-over-top');
                    groupWrapper.classList.remove('drag-over-bottom');
                } else {
                    groupWrapper.classList.add('drag-over-bottom');
                    groupWrapper.classList.remove('drag-over-top');
                }
            }
        });

        groupList.addEventListener('dragleave', (e) => {
            const groupWrapper = e.target.closest('.sidebar-group-wrapper');
            if (groupWrapper) {
                groupWrapper.classList.remove('drag-over-top', 'drag-over-bottom');
            }
        });

        groupList.addEventListener('drop', (e) => {
            e.preventDefault();
            const targetGroup = e.target.closest('.sidebar-group-wrapper');
            
            if (draggedGroup && targetGroup && draggedGroup !== targetGroup) {
                const rect = targetGroup.getBoundingClientRect();
                const midpoint = rect.top + rect.height / 2;
                const insertBefore = e.clientY < midpoint;
                
                // Get new order
                const groups = Array.from(groupList.querySelectorAll('.sidebar-group-wrapper'));
                const targetIndex = groups.indexOf(targetGroup);
                const newOrder = insertBefore ? targetIndex : targetIndex + 1;
                
                // Move in DOM
                if (insertBefore) {
                    groupList.insertBefore(draggedGroup, targetGroup);
                } else {
                    groupList.insertBefore(draggedGroup, targetGroup.nextSibling);
                }
                
                // Update order in database
                const groupId = draggedGroup.dataset.groupId;
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                
                fetch(`/group/${groupId}/reorder/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    },
                    body: `order=${newOrder}`,
                }).catch(err => {
                    console.error('Error reordering group:', err);
                    // Reload page on error
                    window.location.reload();
                });
            }
            
            // Clean up
            groupList.querySelectorAll('.sidebar-group-wrapper').forEach(item => {
                item.classList.remove('drag-over-top', 'drag-over-bottom');
            });
        });
    }
})();
