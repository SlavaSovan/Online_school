<template>
    <button 
        type="button" 
        class="action-icon" 
        :class="variant"
        @click="$emit('click')"
        :title="title"
    >
        <i :class="iconClass"></i>
    </button>
</template>

<script>
export default {
    name: 'action-icon',
    props: {
        variant: {
            type: String,
            default: 'edit',
            validator: (value) => [
                'edit',
                'delete',
                'content',
                'tasks',
                'replace',
                'close',
                'clear',
                'add',
                'activate',
                'deactivate',
                'permissions',
                'star',
            ].includes(value)
        },
        title: {
            type: String,
            default: ''
        }
    },
    computed: {
        iconClass() {
            const icons = {
                edit: 'fas fa-edit',
                delete: 'fas fa-trash-alt',
                content: 'fas fa-file-alt',
                tasks: 'fas fa-tasks',
                replace: 'fas fa-sync-alt',
                close: 'fas fa-times',
                clear: 'fas fa-eraser',
                add: 'fas fa-plus',
                activate: 'fas fa-user-check',
                deactivate: 'fas fa-user-slash',
                permissions: 'fas fa-key',
                star: 'fas fa-star'
            }
            return icons[this.variant] || icons.edit
        }
    },
    emits: ['click']
}
</script>

<style scoped>
.action-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: all 0.2s;
    color: #6c757d;
}

.action-icon i {
    pointer-events: none;
}

.action-icon.edit:hover,
.action-icon.clear:hover,
.action-icon.replace:hover,
.action-icon.star:hover {
    background: #f39c12;
    color: white;
}

.action-icon.delete:hover,
.action-icon.close:hover,
.action-icon.deactivate:hover {
    background: #e74c3c;
    color: white;
}

.action-icon.add:hover,
.action-icon.content:hover,
.action-icon.tasks:hover,
.action-icon.permissions:hover {
    background: #3498db;
    color: white;
}

.action-icon.activate:hover {
    background: #27ae60;;
    color: white;
}
</style>