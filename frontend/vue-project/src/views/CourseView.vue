<template>
    <div class="course-view">
        <div class="course-view__nav">
            <go-back-btn @click="goBack" />
        </div>

        <div v-if="loading" class="course-view__loading">
            Загрузка курса...
        </div>
        
        <div v-else-if="!course">
            Нет данных курса
        </div>
        
        <div v-else class="course-view__content">
            <!-- Хедер курса -->
            <div class="course-header">
                <div class="course-header__top">
                    <div class="course-header__left">
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

                        </div>
                    </div>

                    <div class="course-header__right">
                        <div v-if="isAuthenticated && !checkingEnrollment" class="course-action">
                            <base-button 
                                v-if="!hasAccess"
                                @click="handleEnroll" 
                                :disabled="enrolling"
                                class="action-button enroll-button"
                            >
                                {{ enrolling ? 'Оформление...' : 'Получить' }}
                            </base-button>
                            <base-button 
                                v-else
                                disabled
                                class="action-button obtained-button"
                            >
                                Получено
                            </base-button>
                        </div>
                        
                        <div v-else-if="!isAuthenticated" class="course-action">
                            <base-button 
                                @click="goToLogin"
                                class="login-button"
                            >
                                Получить
                            </base-button>
                        </div>
                        
                        <div v-else-if="checkingEnrollment" class="course-action">
                            <base-button disabled class="action-button loading-button">
                                Проверка...
                            </base-button>
                        </div>
                    </div>
                </div>
                
                <p class="course-description">{{ course.description }}</p>
            </div>
            
            <!-- Модули и уроки -->
            <div class="course-modules">
                <h2 class="modules-title">Содержание курса</h2>
                <ModuleBlock
                    v-for="module in sortedModules"
                    :key="module.id"
                    :module="module"
                    :isContentAvailable="hasAccess"
                    :courseSlug="course.slug"
                    @lesson-click="onLessonClick"
                />
            </div>
            
            <!-- Информация о доступе -->
            <div v-if="!hasAccess && isAuthenticated" class="access-info">
                <i class="fas fa-lock"></i>
                <p>Получите курс, чтобы иметь доступ к материалам</p>
            </div>
            
            <div v-if="!isAuthenticated" class="access-info">
                <i class="fas fa-lock"></i>
                <p><router-link to="/login">Войдите</router-link>, чтобы получить курс</p>
            </div>
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import { useAuthStore } from '@/stores/auth'
import ModuleBlock from '@/components/ModuleBlock.vue'

export default {
    name: 'CourseView',
    components: { ModuleBlock },
    data() {
        return {
            course: null,
            loading: false,
            error: null,
            enrolling: false,
            checkingEnrollment: true,
            hasAccess: false,
        }
    },
    computed: {
        isAuthenticated() {
            const authStore = useAuthStore()
            return authStore.isAuthenticated
        },
        
        isFree() {
            return this.course && parseFloat(this.course.price) === 0
        },
        
        sortedModules() {
            if (!this.course.modules) return []
            return [...this.course.modules].sort((a, b) => a.order - b.order)
        },
    },
    async mounted() {
        await this.loadCourse()
        if (this.isAuthenticated && this.course) {
            await this.checkEnrollment()
        }
        this.checkingEnrollment = false
    },
    watch: {
        async '$route.params.slug'(newSlug) {
            if (newSlug) {
                this.checkingEnrollment = true
                this.loadCourse()
                if (this.isAuthenticated && this.course) {
                    await this.checkEnrollment()
                }
                this.checkingEnrollment = false
            }
        }
    },
    methods: {
        async loadCourse() {
            const slug = this.$route.params.slug

            if (!slug) return
            
            this.loading = true
            this.error = null
            
            try {
                this.course = await coursesApi.getCourseBySlug(slug)
            } catch (err) {
                console.error('Failed to load course:', err)
                if (err.response?.status === 404) {
                    this.error = 'Курс не найден'
                } else {
                    this.error = 'Не удалось загрузить курс'
                }
            } finally {
                this.loading = false
            }
        },
        
        async checkEnrollment() {
            // Проверяем, записан ли пользователь на курс
            try {
                const enrollments = await coursesApi.getMyEnrollments()
                this.hasAccess = enrollments.results?.some(e => e.slug === this.course.slug) || false
            } catch (err) {
                console.error('Failed to check enrollment:', err)
                this.hasAccess = false
            }
        },
        
        goToLogin() {
            this.$router.push('/login')
        },
        
        async handleEnroll() {
            if (!this.isAuthenticated) {
                this.$router.push('/login')
                return
            }
            
            this.enrolling = true
            try {
                await coursesApi.enrollCourse(this.course.slug)
                this.hasAccess = true
                this.$toast.success('Вы успешно записаны на курс!')
            } catch (err) {
                console.error('Failed to enroll:', err)
                this.$toast.error('Не удалось записаться на курс')
            } finally {
                this.enrolling = false
            }
        },
        
        onLessonClick(payload) {
            if (!this.hasAccess) {
                this.$toast.info('Запишитесь на курс, чтобы просматривать уроки')
                return
            }

            const { lesson, moduleSlug } = payload
            
            this.$router.push({
                path: `/course/${this.course.slug}/module/${moduleSlug}/lesson/${lesson.slug}`,
                query: { title: lesson.title }
            })
        },
        
        goBack() {
            this.$router.push('/my-courses')
        }
    }
}
</script>

<style scoped>
.course-view {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.course-view__nav {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.course-view__loading,
.course-view__error {
    text-align: center;
    padding: 3rem;
}

.course-view__error {
    color: #e74c3c;
}

.course-header {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.course-header__top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
    margin-bottom: 1rem;
}

.course-header__left {
    flex: 1;
}

.course-header__right {
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    min-width: 180px;
}

.course-title {
    font-size: 2rem;
    color: #2c3e50;
    margin: 0 0 1rem 0;
}

.course-action {
    width: 100%;
    max-width: 180px;
}

.enroll-button,
.obtained-button,
.login-button,
.loading-button {
    width: 100%;
    text-align: center;
}

.enroll-button :deep(.btn) {
    background: #3498db;
    color: white;
}

.enroll-button :deep(.btn:hover:not(:disabled)) {
    background: #2980b9;
    transform: translateY(-2px);
}

.obtained-button :deep(.btn) {
    background: #f8f9fa;
    color: #6c757d;
    border: 2px solid #dee2e6;
    cursor: default;
}

.obtained-button :deep(.btn:hover) {
    background: #f8f9fa;
    transform: none;
}

.login-button :deep(.btn) {
    background: #95a5a6;
    color: white;
}

.login-button :deep(.btn:hover) {
    background: #7f8c8d;
}

.loading-button :deep(.btn) {
    background: #95a5a6;
    color: white;
    cursor: wait;
    opacity: 0.6;
}

.course-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
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

.access-info {
    margin-top: 2rem;
    padding: 1.5rem;
    background: #fff3cd;
    border-radius: 12px;
    text-align: center;
    color: #856404;
}

.access-info i {
    font-size: 1.5rem;
}

.access-info a {
    color: #3498db;
    text-decoration: none;
}

.access-info a:hover {
    text-decoration: underline;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@media (max-width: 768px) {
    .course-header__top {
        flex-direction: column;
    }
    
    .course-header__right {
        justify-content: flex-start;
        align-items: flex-start;
    }
    
    .course-title {
        font-size: 1.5rem;
    }
    
    .course-action {
        max-width: none;
    }
}
</style>