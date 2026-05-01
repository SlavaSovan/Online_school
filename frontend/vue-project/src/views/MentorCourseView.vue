<template>
    <div class="mentor-course-view">
        <div class="mentor-course-view__nav">
            <go-back-btn @click="goBack" />
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="mentor-course-view__loading">
            Загрузка курса...
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="mentor-course-view__error">
            <p>{{ error }}</p>
            <base-button @click="loadCourse">Повторить</base-button>
        </div>

        <!-- Контент курса -->
        <div v-else-if="course" class="mentor-course-view__content">
            <!-- Хедер курса -->
            <div class="course-header">
                <h1 class="course-title">{{ course.title }}</h1>
                <div class="course-meta">
                    <span class="course-lessons">
                        <i class="fas fa-book-open"></i>
                        {{ course.lessons_count }} уроков
                    </span>
                    <span class="course-price" :class="{ free: isFree }">
                        <i class="fas fa-tag"></i>
                        {{ isFree ? 'Бесплатно' : `${course.price} ₽` }}
                    </span>
                    <span class="course-status" :class="statusClass">
                        <i class="fas fa-info-circle"></i>
                        {{ statusLabel }}
                    </span>
                </div>
                <p class="course-description">{{ course.description }}</p>
            </div>

            <!-- Модули и уроки с контентом и заданиями -->
            <div class="course-modules">
                <h2 class="modules-title">Содержание курса</h2>
                <MentorModuleBlock
                    v-for="module in sortedModules"
                    :key="module.id"
                    :module="module"
                    :courseSlug="course.slug"
                />
            </div>
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import MentorModuleBlock from '@/components/MentorModuleBlock.vue'

export default {
    name: 'MentorCourseView',
    components: { MentorModuleBlock },
    data() {
        return {
            course: null,
            loading: false,
            error: null
        }
    },
    computed: {
        courseSlug() {
            return this.$route.params.courseSlug
        },
        isFree() {
            return this.course && parseFloat(this.course.price) === 0
        },
        statusLabel() {
            const labels = {
                draft: 'Черновик',
                published: 'Опубликован',
                archived: 'Архивирован'
            }
            return labels[this.course?.status] || this.course?.status
        },
        statusClass() {
            const classes = {
                draft: 'status-draft',
                published: 'status-published',
                archived: 'status-archived'
            }
            return classes[this.course?.status] || ''
        },
        sortedModules() {
            if (!this.course?.modules) return []
            return [...this.course.modules].sort((a, b) => a.order - b.order)
        }
    },
    async mounted() {
        await this.loadCourse()
    },
    watch: {
        courseSlug() {
            this.loadCourse()
        }
    },
    methods: {
        async loadCourse() {
            const slug = this.courseSlug

            if (!slug) return
            
            this.loading = true
            this.error = null
            
            try {
                // Используем приватный эндпоинт для получения курса (включая черновики)
                this.course = await coursesApi.getPrivateCourseBySlug(slug)
            } catch (err) {
                console.error('Failed to load course:', err)
                if (err.response?.status === 404) {
                    this.error = 'Курс не найден'
                } else if (err.response?.status === 403) {
                    this.error = 'У вас нет доступа к этому курсу'
                } else {
                    this.error = 'Не удалось загрузить курс'
                }
            } finally {
                this.loading = false
            }
        },
        
        goBack() {
            this.$router.push('/my-courses')
        }
    }
}
</script>

<style scoped>
.mentor-course-view {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.mentor-course-view__nav {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.mentor-course-title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 0;
}

.mentor-course-view__loading,
.mentor-course-view__error {
    text-align: center;
    padding: 3rem;
}

.mentor-course-view__error {
    color: #e74c3c;
}

.course-header {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.course-title {
    font-size: 2rem;
    color: #2c3e50;
    margin: 0 0 1rem 0;
}

.course-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.course-lessons {
    background: #e3f2fd;
    color: #1976d2;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.course-price {
    background: #e8f5e9;
    color: #388e3c;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: bold;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.course-price.free {
    background: #e8f5e9;
    color: #27ae60;
}

.course-status {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.status-draft {
    background: #fff3cd;
    color: #856404;
}

.status-published {
    background: #d4edda;
    color: #155724;
}

.status-archived {
    background: #f8d7da;
    color: #721c24;
}

.course-description {
    color: #6c757d;
    line-height: 1.6;
    margin: 1rem 0 0 0;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}

.course-modules {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.modules-title {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #2c3e50;
}

@media (max-width: 768px) {
    .mentor-course-view__nav {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .course-title {
        font-size: 1.5rem;
    }
}
</style>