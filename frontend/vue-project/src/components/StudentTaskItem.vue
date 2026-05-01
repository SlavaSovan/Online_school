<template>
    <div class="student-task-item" @click="$emit('click')">
        <div class="task-order">{{ order }}.</div>
        <div class="task-info">
            <div class="task-header">
                <div class="task-title">{{ task.title }}</div>
                <div class="task-badges">
                    <badge variant="primary" :label="getTaskTypeLabel()" />
                </div>
            </div>
            <div class="task-stats">
                <div class="stat-item">
                    <span class="stat-label">Статус:</span>
                    <badge :variant="getStatusVariant()" :label="getStatusLabel()" size="small" />
                </div>
                <div class="stat-item">
                    <span class="stat-label">Попытки:</span>
                    <span class="stat-value">{{ attemptsUsed }} / {{ maxAttempts === 0 ? '∞' : maxAttempts }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Балл:</span>
                    <span class="stat-value">{{ lastScore !== null ? lastScore : '-' }} / {{ maxScore }}</span>
                </div>
            </div>
        </div>
        <div class="task-arrow">
            <i class="fas fa-chevron-right"></i>
        </div>
    </div>
</template>

<script>
export default {
    name: 'StudentTaskItem',
    props: {
        task: {
            type: Object,
            required: true
        },
        order: {
            type: Number,
            required: true
        },
        // Дополнительные данные для отображения статуса
        attemptsUsed: {
            type: Number,
            default: 0
        },
        maxAttempts: {
            type: Number,
            default: 0
        },
        maxScore: {
            type: Number,
            default: 100
        },
        lastScore: {
            type: Number,
            default: null
        },
        status: {
            type: String,
            default: 'not_started' // not_started, needs_review, passed, failed
        }
    },
    computed: {
        isTest() {
            return this.task.task_type === 'test'
        },
        isFile() {
            return this.task.task_type === 'file_upload'
        },
        isSandbox() {
            return this.task.task_type === 'sandbox'
        }
    },
    methods: {
        getTaskTypeLabel() {
            const labels = {
                test: 'Тест',
                file_upload: 'Файл',
                sandbox: 'Код'
            }
            return labels[this.task.task_type] || this.task.task_type
        },
        
        getStatusVariant() {
            const variants = {
                not_started: 'info',
                needs_review: 'warning',
                passed: 'success',
                failed: 'danger'
            }
            return variants[this.status] || 'info'
        },
        
        getStatusLabel() {
            const labels = {
                not_started: 'Не начато',
                needs_review: 'На проверке',
                passed: 'Зачтено',
                failed: 'Не зачтено'
            }
            return labels[this.status] || this.status
        }
    },
    emits: ['click']
}
</script>

<style scoped>
.student-task-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    cursor: pointer;
    transition: all 0.2s;
}

.student-task-item:hover {
    background: #e9ecef;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-order {
    font-weight: bold;
    font-size: 1.1rem;
    color: #3498db;
    min-width: 35px;
}

.task-info {
    flex: 1;
}

.task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.task-title {
    font-weight: 500;
    color: #2c3e50;
}

.task-badges {
    display: flex;
    gap: 0.5rem;
}

.task-stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
}

.stat-label {
    color: #7f8c8d;
}

.stat-value {
    font-weight: 500;
    color: #2c3e50;
}

.task-arrow {
    color: #bdc3c7;
    font-size: 0.875rem;
    transition: transform 0.2s;
}

.student-task-item:hover .task-arrow {
    transform: translateX(4px);
    color: #3498db;
}
</style>