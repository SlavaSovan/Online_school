<template>
    <span class="badge" :class="variant">
        <i v-if="icon" :class="icon"></i>
        {{ label }}
    </span>
</template>

<script>
export default {
    name: 'badge',
    props: {
        variant: {
            type: String,
            default: 'published',
            validator: (value) => [
                'published',
                'draft',
                'content',
                'tasks',
                'primary', 
                'info',
                'success',
                'warning',
                'danger',
            ].includes(value)
        },
        label: {
            type: String,
            default: ''
        },
        icon: {
            type: String,
            default: ''
        }
    }
}
</script>

<style scoped>
.badge {
    font-size: 0.7rem;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.badge i {
    font-size: 0.65rem;
}

.badge.published {
    background: #e8f5e9;
    color: #388e3c;
}

.badge.draft {
    background: #fff3e0;
    color: #f39c12;
}

.badge.content {
    background: #e3f2fd;
    color: #1976d2;
}

.badge.tasks {
    background: #e3f2fd;
    color: #1976d2;
}

.badge.primary {
    background: #e3f2fd;
    color: #1976d2;
}

.badge.info {
    background: #e1f5fe;
    color: #0288d1;
}

.badge.success {
    background: #e8f5e9;
    color: #2e7d32;
}

.badge.warning {
    background: #fff3e0;
    color: #f57c00;
}

.badge.danger {
    background: #ffebee;
    color: #d32f2f;
}
</style>