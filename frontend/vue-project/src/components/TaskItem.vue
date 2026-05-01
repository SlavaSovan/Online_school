<template>
    <div class="task-item" draggable="true" @dragstart="onDragStart" @dragover.prevent @dragend="onDragEnd">
        <div class="drag-handle">⋮⋮</div>
        <div class="task-info" @click="editTask">
            <div class="task-header">
                <div class="task-order">{{ order }}.</div>
                <div class="task-title">{{ task.title }}</div>
                <div class="task-badges">
                    <badge variant="primary" :label="getTaskTypeLabel()" />
                    <badge v-if="task.max_attempts > 0" variant="info" :label="`${task.max_attempts} попыток`" />
                </div>
            </div>
            <div class="task-meta">
                <span class="task-score">Макс. балл: {{ task.max_score }}</span>
            </div>
        </div>
        <div class="task-actions">
            <action-icon variant="edit" @click="editTask" title="Редактировать" />
            <action-icon variant="delete" @click="deleteTask" title="Удалить" />
        </div>
    </div>
</template>

<script>
export default {
    name: 'TaskItem',
    props: {
        task: {
            type: Object,
            required: true
        },
        order: {
            type: Number,
            required: true
        },
        index: {
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
        
        onDragStart(event) {
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', this.index)
            this.$emit('drag-start', this.index)
        },
        
        onDragEnd() {
            this.$emit('drag-end')
        },
        
        editTask() {
            this.$emit('edit', this.task)
        },
        
        deleteTask() {
            this.$emit('delete', this.task)
        }
    },
    emits: ['drag-start', 'drag-end', 'edit', 'delete']
}
</script>

<style scoped>
.task-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    transition: all 0.2s;
    cursor: grab;
}

.task-item:hover {
    background: #e9ecef;
}

.task-item:active {
    cursor: grabbing;
}

.drag-handle {
    cursor: grab;
    color: #adb5bd;
    font-size: 1.2rem;
    user-select: none;
}

.drag-handle:active {
    cursor: grabbing;
}

.task-info {
    flex: 1;
    cursor: pointer;
}

.task-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}

.task-order {
    font-weight: bold;
    color: #3498db;
}

.task-title {
    font-weight: 500;
    color: #2c3e50;
}

.task-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.task-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: #7f8c8d;
}

.task-score {
    background: #e8f5e9;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    color: #2e7d32;
}

.task-actions {
    display: flex;
    gap: 0.5rem;
}
</style>