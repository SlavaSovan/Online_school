<template>
    <div class="mentor-lesson-block">
        <div class="lesson-header" @click="toggleExpand"">
            <div class="lesson-header__left">
                <span class="lesson-order">{{ order }}.</span>
                <h3 class="lesson-title">{{ lesson.title }}</h3>
            </div>
            <span class="lesson-expand">{{ isExpanded ? '▼' : '▶' }}</span>
        </div>
        
        <div v-show="isExpanded" class="lesson-content">
            <!-- Контент урока -->
            <div class="content-section">
                <div class="content-header">
                    <h4>Контент</h4>
                    <base-button 
                        v-if="lesson.content && lesson.content.length > 0"
                        variant="primary" 
                        size="small"
                        @click="goToContent"
                    >
                        Перейти к контенту
                    </base-button>
                    <span v-else class="no-content">Нет контента</span>
                </div>
            </div>

            <!-- Задания урока -->
            <div class="tasks-section">
                <div class="tasks-header">
                    <h4>Задания</h4>
                    <div v-if="loadingTasks" class="tasks-loading">Загрузка...</div>
                </div>
                <div v-if="!loadingTasks && tasks.length > 0" class="tasks-list">
                    <MentorTaskItem
                        v-for="(task, idx) in sortedTasks"
                        :key="task.id"
                        :task="task"
                        :order="idx + 1"
                        @click="goToTask(task)"
                    />
                </div>
                <div v-else-if="!loadingTasks && tasks.length === 0" class="tasks-empty">
                    <p>Нет заданий</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { tasksApi } from '@/api/endpoints/tasks'
import MentorTaskItem from './MentorTaskItem.vue'

export default {
    name: 'MentorLessonBlock',
    components: { MentorTaskItem },
    props: {
        lesson: {
            type: Object,
            required: true
        },
        order: {
            type: Number,
            required: true
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
    data() {
        return {
            isExpanded: true,
            tasks: [],
            loadingTasks: false,
        }
    },
    computed: {
        sortedTasks() {
            return [...this.tasks].sort((a, b) => a.order - b.order)
        }
    },
    mounted() {
        if (this.isExpanded) {
            this.loadTasks()
        }
    },
    methods: {
        async toggleExpand() {
            this.isExpanded = !this.isExpanded
            if (this.isExpanded && this.tasks.length === 0) {
                await this.loadTasks()
            }
        },
        
        async loadTasks() {
            this.loadingTasks = true
            try {
                const response = await tasksApi.getLessonTasks(
                    this.courseSlug,
                    this.moduleSlug,
                    this.lesson.slug
                )
                this.tasks = response || []
            } catch (err) {
                console.error('Failed to load tasks:', err)
                this.tasks = []
            } finally {
                this.loadingTasks = false
            }
        },

        goToContent() {
            this.$router.push({
                path: `/mentoring/course/${this.courseSlug}/module/${this.moduleSlug}/lesson/${this.lesson.slug}/content`,
                query: { title: this.lesson.title }
            })
        },
        
        goToTask(task) {
            this.$router.push({
                path: `/mentoring/course/${this.courseSlug}/module/${this.moduleSlug}/lesson/${this.lesson.slug}/task/${task.id}`,
                query: { 
                    taskTitle: task.title,
                    taskType: task.task_type
                }
            })
        }
    }
}
</script>

<style scoped>
.mentor-lesson-block {
    background: white;
    border-radius: 8px;
    margin-bottom: 1rem;
    overflow: hidden;
    border: 1px solid #e9ecef;
}

.lesson-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    background: #f8f9fa;
    cursor: pointer;
    transition: background 0.2s;
}

.lesson-header:hover {
    background: #e9ecef;
}

.lesson-header__left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.lesson-order {
    font-weight: bold;
    color: #3498db;
}

.lesson-title {
    margin: 0;
    font-size: 1.1rem;
    color: #2c3e50;
}

.lesson-expand {
    color: #7f8c8d;
    font-size: 0.75rem;
}

.lesson-content {
    padding: 1.25rem;
}

.content-section,
.tasks-section {
    margin-bottom: 1.5rem;
}

.content-section:last-child,
.tasks-section:last-child {
    margin-bottom: 0;
}

.content-header {
    display: flex;
    flex-direction: column;
    width: 200px;
}

.content-header h4,
.tasks-section h4 {
    margin-bottom: 1rem;
    font-size: 1rem;
    color: #2c3e50;
}

.no-content {
    font-size: 0.875rem;
    color: #7f8c8d;
}

.tasks-loading {
    font-size: 0.75rem;
    color: #7f8c8d;
}

.tasks-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.tasks-section.empty {
    text-align: center;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 6px;
    color: #7f8c8d;
    font-size: 0.875rem;
}
</style>