<template>
    <div class="lesson-view">
        <!-- Навигация -->
        <div class="lesson-view__nav">
            <go-back-btn @click="goBack" />
            <h1 class="lesson-title">{{ lessonTitle }}</h1>
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="lesson-view__loading">
            Загрузка контента...
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="lesson-view__error">
            <p>{{ error }}</p>
            <base-button @click="loadContent">Повторить</base-button>
        </div>

        <!-- Контент -->
        <div v-else class="lesson-view__content">
            <div 
                v-for="item in sortedContent" 
                :key="item.id"
                class="content-item"
            >
                <!-- Markdown контент -->
                <ContentMarkdown
                    v-if="item.content_type === 'markdown'"
                    :content="markdownContents[item.id]"
                    :filename="item.filename"
                    :originalFilename="item.original_filename"
                    :fileUrl="item.file_url"
                />
                
                <!-- Изображения -->
                <ContentImage
                    v-else-if="item.content_type === 'image'"
                    :fileUrl="item.file_url"
                    :filename="item.filename"
                    :originalFilename="item.original_filename"
                />
                
                <!-- Видео -->
                <ContentVideo
                    v-else-if="item.content_type === 'video'"
                    :fileUrl="item.file_url"
                    :filename="item.filename"
                    :originalFilename="item.original_filename"
                />
                
                <!-- Другие файлы -->
                <ContentFile
                    v-else
                    :fileUrl="item.file_url"
                    :filename="item.filename"
                    :originalFilename="item.original_filename"
                    :fileSize="item.file_size"
                />
            </div>
            
            <div v-if="sortedContent.length === 0" class="lesson-view__empty">
                <p>В этом уроке пока нет контента</p>
            </div>
        </div>

        <!-- Задания -->
        <div v-if="isEnrolled && tasks.length > 0" class="lesson-tasks">
            <div class="lesson-view__nav">
                <h2 class="tasks-title">Задания</h2>
            </div>
            <div class="tasks-list">
                <StudentTaskItem
                    v-for="(task, index) in sortedTasks"
                    :key="task.id"
                    :task="task"
                    :order="index + 1"
                    :attempts-used="task.attemptsUsed"
                    :max-attempts="task.maxAttempts"
                    :max-score="task.maxScore"
                    :last-score="task.lastScore"
                    :status="task.status"
                    @click="goToTask(task)"
                />
            </div>
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import { tasksApi } from '@/api/endpoints/tasks'
import ContentMarkdown from '@/components/content/ContentMarkdown.vue'
import ContentImage from '@/components/content/ContentImage.vue'
import ContentVideo from '@/components/content/ContentVideo.vue'
import ContentFile from '@/components/content/ContentFile.vue'
import StudentTaskItem from '@/components/StudentTaskItem.vue'

export default {
    name: 'LessonView',
    components: {
        ContentMarkdown,
        ContentImage,
        ContentVideo,
        ContentFile,
        StudentTaskItem
    },
    data() {
        return {
            content: [],
            loading: false,
            error: null,
            markdownContents: {},
            tasks: [],
            isEnrolled: false,
        }
    },
    computed: {
        courseSlug() {
            return this.$route.params.courseSlug
        },
        moduleSlug() {
            return this.$route.params.moduleSlug
        },
        lessonSlug() {
            return this.$route.params.lessonSlug
        },
        lessonTitle() {
            return this.$route.query.title || 'Урок'
        },
        sortedContent() {
            return [...this.content].sort((a, b) => a.order - b.order)
        },
        sortedTasks() {
            return [...this.tasks].sort((a, b) => a.order - b.order)
        }
    },
    async mounted() {
        await this.loadContent()
        await this.checkEnrollment()
        if (this.isEnrolled) {
            await this.loadTasks()
        }
    },
    watch: {
        lessonSlug() {
            this.loadContent()
        }
    },
    methods: {
        async loadContent() {
            if (!this.courseSlug || !this.moduleSlug || !this.lessonSlug) {
                this.error = 'Неверные параметры урока'
                return
            }
            
            this.loading = true
            this.error = null
            this.content = []
            this.markdownContents = {}
            
            try {
                // Загружаем список контента
                const response = await coursesApi.getLessonContent(
                    this.courseSlug,
                    this.moduleSlug,
                    this.lessonSlug
                )
                
                this.content = response.results || []
                
                // Загружаем содержимое markdown файлов
                for (const item of this.content) {
                    if (item.content_type === 'markdown') {
                        try {
                            const markdownData = await coursesApi.getMarkdownContent(
                                this.courseSlug,
                                this.moduleSlug,
                                this.lessonSlug,
                                item.id
                            )
                            this.markdownContents[item.id] = markdownData.content || ''
                        } catch (err) {
                            console.error(`Failed to load markdown content for ${item.id}:`, err)
                            this.markdownContents[item.id] = 'Ошибка загрузки содержимого'
                        }
                    }
                }
            } catch (err) {
                console.error('Failed to load lesson content:', err)
                if (err.response?.status === 403) {
                    this.error = 'У вас нет доступа к этому уроку'
                } else if (err.response?.status === 404) {
                    this.error = 'Урок не найден'
                } else {
                    this.error = 'Не удалось загрузить содержимое урока'
                }
            } finally {
                this.loading = false
            }
        },
        
        goBack() {
            this.$router.push(`/course/${this.courseSlug}`)
        },

        async loadTasks() {
            try {
                const tasks = await tasksApi.getLessonTasks(
                    this.courseSlug, 
                    this.moduleSlug, 
                    this.lessonSlug
                )
                
                // Для каждого задания получаем состояние
                const tasksWithState = await Promise.all(
                    tasks.map(async (task) => {
                        try {
                            const state = await tasksApi.getTaskState(task.id)
                            return {
                                ...task,
                                attemptsUsed: state.attempts_used || 0,
                                maxAttempts: state.max_attempts || 0,
                                maxScore: state.max_score || 0,
                                lastScore: state.last_submission?.score || null,
                                status: this.getTaskStatus(state)
                            }
                        } catch (err) {
                            console.error(`Failed to get state for task ${task.id}:`, err)
                            return {
                                ...task,
                                attemptsUsed: 0,
                                maxAttempts: task.max_attempts || 0,
                                maxScore: task.max_score || 0,
                                lastScore: null,
                                status: 'not_started'
                            }
                        }
                    })
                )
                
                this.tasks = tasksWithState
            } catch (err) {
                console.error('Failed to load tasks:', err)
                this.tasks = []
            }
        },

        getTaskStatus(state) {
            if (!state.last_submission) {
                return 'not_started'
            }
            
            const status = state.last_submission.status
            
            if (status === 'passed') {
                return 'passed'
            }
            
            if (status === 'failed') {
                return 'failed'
            }
            
            if (status === 'needs_review') {
                return 'needs_review'
            }
            
            return 'not_started'
        },

        async checkEnrollment() {
            try {
                const enrollments = await coursesApi.getMyEnrollments()
                this.isEnrolled = enrollments.results?.some(e => e.slug === this.courseSlug) || false
            } catch (err) {
                console.error('Failed to check enrollment:', err)
                this.isEnrolled = false
            }
        },

        goToTask(task) {
            if (!this.isEnrolled) {
                this.$toast.warning('Запишитесь на курс, чтобы выполнять задания')
                return
            }
            
            let routePath = ''
            switch (task.task_type) {
                case 'test':
                    routePath = `/task/${task.id}/test`
                    break
                case 'file_upload':
                    routePath = `/task/${task.id}/file`
                    break
                case 'sandbox':
                    routePath = `/task/${task.id}/sandbox`
                    break
                default:
                    this.$toast.warning('Неизвестный тип задания')
                    return
            }
            
            this.$router.push({
                path: routePath,
                query: {
                    courseSlug: this.courseSlug,
                    moduleSlug: this.moduleSlug,
                    lessonSlug: this.lessonSlug,
                    title: task.title,
                    description: task.description
                }
            })
        },
    }
}
</script>

<style scoped>
.lesson-view {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.lesson-view__nav {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.lesson-title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 0;
}

.lesson-view__loading,
.lesson-view__error,
.lesson-view__empty {
    text-align: center;
    padding: 3rem;
}

.lesson-view__error {
    color: #e74c3c;
}

.lesson-view__empty {
    color: #7f8c8d;
}

.lesson-view__content {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.content-item {
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}

.content-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.tasks-title {
    margin-top: 1rem;
}
</style>