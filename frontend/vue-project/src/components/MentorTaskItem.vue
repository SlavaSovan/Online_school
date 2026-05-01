<template>
    <div class="mentor-task-item" @click="$emit('click')">
        <div class="task-order">{{ order }}.</div>
        <div class="task-info">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-badges">
                <badge variant="primary" :label="getTaskTypeLabel()" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'MentorTaskItem',
    props: {
        task: {
            type: Object,
            required: true
        },
        order: {
            type: Number,
            required: true
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
    },
    emits: ['click']
}
</script>

<style scoped>
.mentor-task-item {
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

.mentor-task-item:hover {
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
    display: flex;
    flex: 1;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
}

.task-title {
    font-weight: 500;
    color: #2c3e50;
}

.task-badges {
    display: flex;
    gap: 0.5rem;
}

.task-description {
    font-size: 0.875rem;
    color: #6c757d;
    margin-top: 0.25rem;
}

.mentor-task-item:hover {
    transform: translateX(4px);
    color: #3498db;
}
</style>