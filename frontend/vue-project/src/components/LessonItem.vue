<template>
    <div class="lesson-item" @click="$emit('click', lesson)">
        <div class="lesson-info">
            <span class="lesson-order">{{ lesson.order }}.</span>
            <span class="lesson-title">{{ lesson.title }}</span>
        </div>
        <div class="lesson-status">
            <badge v-if="hasContent" variant="content" label="Контент"/>
            <badge v-if="hasTasks" variant="tasks" label="Задания"/>
            <span v-if="!isContentAvailable" class="lock-icon">
                <i class="fa fa-lock" aria-hidden="true"></i>
            </span>
        </div>
    </div>
</template>

<script>
export default {
    name: 'LessonItem',
    props: {
        lesson: {
            type: Object,
            required: true
        },
        isContentAvailable: {
            type: Boolean,
            default: false
        },
        courseSlug: {
            type: String,
            required: true
        },
        moduleSlug: {
            type: String,
            required: true
        }
    },
    computed: {
        hasContent() {
            return this.lesson.content && this.lesson.content.length > 0
        },
        hasTasks() {
            return this.lesson.tasks && this.lesson.tasks.length > 0
        }
    },
    methods: {
        handleClick() {
            // Просто передаем урок в родительский компонент
            this.$emit('click', this.lesson)
        }
    },
    emits: ['click']
}
</script>

<style scoped>
.lesson-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #f8f9fa;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}

.lesson-item:hover {
    background: #e9ecef;
}

.lesson-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.lesson-order {
    color: #7f8c8d;
    font-size: 0.875rem;
}

.lesson-title {
    color: #2c3e50;
    font-size: 0.875rem;
}

.lesson-status {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
}

.lock-icon {
    font-size: 0.875rem;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: all 0.2s;
    color: #6c757d;
}

.lock-icon i {
    pointer-events: none;
}
</style>