<template>
    <div class="module-block">
        <div class="module-header" @click="isExpanded = !isExpanded">
            <div class="module-header__left">
                <span class="module-order">{{ module.order }}.</span>
                <h3 class="module-title">{{ module.title }}</h3>
            </div>
            <span class="module-expand">{{ isExpanded ? '▼' : '▶' }}</span>
        </div>
        
        <div v-show="isExpanded" class="module-content">
            <p v-if="module.description" class="module-description">{{ module.description }}</p>
            <div class="lessons-list">
                <LessonItem
                    v-for="lesson in sortedLessons"
                    :key="lesson.id"
                    :lesson="lesson"
                    :isContentAvailable="isContentAvailable"
                    :courseSlug="courseSlug"
                    :moduleSlug="module.slug"
                    @click="onLessonClick"
                />
            </div>
        </div>
    </div>
</template>

<script>
import LessonItem from './LessonItem.vue'

export default {
    name: 'ModuleBlock',
    components: { LessonItem },
    props: {
        module: {
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
        }
    },
    data() {
        return {
            isExpanded: true
        }
    },
    computed: {
        sortedLessons() {
            if (!this.module.lessons) return []
            return [...this.module.lessons].sort((a, b) => a.order - b.order)
        }
    },
    methods: {
        onLessonClick(lesson) {
            if (!this.isContentAvailable) {
                this.$emit('lesson-click', lesson)
                return
            }
            
            this.$emit('lesson-click', {
                lesson,
                moduleSlug: this.module.slug
            })
        }
    },
    emits: ['lesson-click']
}
</script>

<style scoped>
.module-block {
    background: white;
    border-radius: 8px;
    margin-bottom: 1rem;
    overflow: hidden;
    border: 1px solid #e9ecef;
}

.module-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    background: #f8f9fa;
    cursor: pointer;
    transition: background 0.2s;
}

.module-header:hover {
    background: #e9ecef;
}

.module-header__left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.module-order {
    font-weight: bold;
    color: #2c3e50;
}

.module-title {
    margin: 0;
    font-size: 1.1rem;
    color: #2c3e50;
}

.module-expand {
    color: #7f8c8d;
    font-size: 0.75rem;
}

.module-content {
    padding: 1.25rem;
}

.module-description {
    color: #6c757d;
    margin-bottom: 1rem;
    font-size: 0.875rem;
}

.lessons-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
</style>