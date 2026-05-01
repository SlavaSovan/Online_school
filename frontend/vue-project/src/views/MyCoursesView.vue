<template>
    <div class="my-courses">
        <h1 class="my-courses__title">Мои курсы</h1>

        <div v-if="isMentor" class="courses-section">
            <div class="section-header">
                <h2 class="section-title">Мои курсы</h2>
                <router-link to="/course/create" class="create-link">
                    <base-button variant="primary">+ Создать курс</base-button>
                </router-link>
            </div>
            
            <div v-if="loadingOwnerCourses" class="loading">
                Загрузка...
            </div>
            
            <div v-else-if="ownerCourses.length === 0" class="empty">
                <p>У вас пока нет курсов</p>
                <router-link to="/course/create" class="catalog-link">Создать курс</router-link>
            </div>
            
            <div v-else class="courses-grid">
                <course-card
                    v-for="course in ownerCourses"
                    :key="course.id"
                    :course="course"
                    @click="goToEditCourse(course.slug)"
                />
        
                <!-- Карточка для создания нового курса -->
                <div class="create-course-card" @click="goToCreateCourse">
                    <div class="create-course-card__content">
                        <div class="create-icon">+</div>
                        <p>Создать курс</p>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="isMentor" class="courses-section">
            <h2 class="section-title">Менторство</h2>
            
            <div v-if="loadingMentorCourses" class="loading">
                Загрузка...
            </div>
            
            <div v-else-if="mentorCourses.length === 0" class="empty">
                <p>Вы пока не являетесь ментором ни одного курса</p>
            </div>
            
            <div v-else class="courses-grid">
                <course-card
                    v-for="course in mentorCourses"
                    :key="course.id"
                    :course="course"
                    @click="goToMentorCourse(course.slug)"
                />
            </div>
        </div>
        
        <div class="courses-section">
            <h2 class="section-title">Приобретенные курсы</h2>
            
            <div v-if="loading" class="loading">
                Загрузка...
            </div>
            
            <div v-else-if="error" class="error">
                {{ error }}
                <base-button @click="loadEnrollments">Повторить</base-button>
            </div>
            
            <div v-else-if="enrollments.length === 0" class="empty">
                <p>У вас пока нет приобретенных курсов</p>
                <router-link to="/catalog" class="catalog-link">Перейти в каталог</router-link>
            </div>
            
            <div v-else class="courses-grid">
                <course-card
                    v-for="course in enrollments"
                    :key="course.id"
                    :course="course"
                    @click="goToCourse(course.slug)"
                />
            </div>
            
            <div v-if="hasMore" class="load-more">
                <base-button @click="loadMore" :disabled="loadingMore">
                    {{ loadingMore ? 'Загрузка...' : 'Загрузить еще' }}
                </base-button>
            </div>
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import { useAuthStore } from '@/stores/auth'
import CourseCard from '@/components/CourseCard.vue'

export default {
    name: 'MyCoursesView',
    components: { CourseCard },
    data() {
        return {
            // Приобретенные курсы (ученик)
            enrollments: [],
            loading: false,
            loadingMore: false,
            error: null,
            nextCursor: null,
            hasMore: true,
            
            // Курсы, где пользователь является владельцем
            ownerCourses: [],
            loadingOwnerCourses: false,
            
            // Курсы, где пользователь является ментором
            mentorCourses: [],
            loadingMentorCourses: false,
        }
    },
    computed: {
        isMentor() {
            const authStore = useAuthStore()
            return authStore.isMentor
        }
    },
    async mounted() {
        await this.loadEnrollments()
        
        if (this.isMentor) {
            await Promise.all([
                this.loadOwnerCourses(),
                this.loadMentorCourses()
            ])
        }
    },
    methods: {
        async loadEnrollments(reset = true) {
            if (reset) {
                this.loading = true
                this.enrollments = []
                this.nextCursor = null
                this.hasMore = true
            } else {
                this.loadingMore = true
            }
            
            try {
                const params = {}
                if (this.nextCursor) {
                    params.cursor = this.nextCursor
                }
                
                const response = await coursesApi.getMyEnrollments(params)
                
                if (reset) {
                    this.enrollments = response.results || []
                } else {
                    this.enrollments = [...this.enrollments, ...(response.results || [])]
                }
                
                this.nextCursor = response.next ? this.extractCursor(response.next) : null
                this.hasMore = !!response.next
                
                this.error = null
            } catch (err) {
                this.error = 'Не удалось загрузить курсы'
            } finally {
                this.loading = false
                this.loadingMore = false
            }
        },
        
        // Загрузка курсов, где пользователь является владельцем
        async loadOwnerCourses() {
            this.loadingOwnerCourses = true
            
            try {
                const response = await coursesApi.getMyOwnerCourses()
                this.ownerCourses = response.results || []
            } catch (err) {
                this.ownerCourses = []
            } finally {
                this.loadingOwnerCourses = false
            }
        },
        
        // Загрузка курсов, где пользователь является ментором (но не владельцем)
        async loadMentorCourses() {
            this.loadingMentorCourses = true
            
            try {
                const response = await coursesApi.getMyMentorCourses()
                this.mentorCourses = response.results || []
            } catch (err) {
                this.mentorCourses = []
            } finally {
                this.loadingMentorCourses = false
            }
        },
        
        extractCursor(url) {
            if (!url) return null
            const match = url.match(/cursor=([^&]+)/)
            return match ? match[1] : null
        },
        
        async loadMore() {
            if (this.hasMore && !this.loading && !this.loadingMore) {
                await this.loadEnrollments(false)
            }
        },
        
        goToCourse(slug) {
            this.$router.push(`/course/${slug}`)
        },

        goToMentorCourse(slug) {
            this.$router.push(`/mentoring/course/${slug}`)
        },
                
        goToEditCourse(slug) {
            this.$router.push(`/course/${slug}/edit`)
        },

        goToCreateCourse() {
            this.$router.push('/course/create')
        }
    }
}
</script>

<style scoped>
.my-courses {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.my-courses__title {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #2c3e50;
}

.courses-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #2c3e50;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
}

.mentor-section .section-title {
    border-bottom-color: #f39c12;
}.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.section-header .section-title {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.create-link {
    text-decoration: none;
}

.create-course-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 2px dashed #3498db;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
}

.create-course-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    border-color: #2980b9;
    background: #f8f9fa;
}

.create-course-card__content {
    text-align: center;
}

.create-icon {
    font-size: 3rem;
    color: #3498db;
    margin-bottom: 0.5rem;
}

.create-course-card p {
    color: #7f8c8d;
    margin: 0;
}

.courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
}

.loading, .error, .empty {
    text-align: center;
    padding: 3rem;
}

.error {
    color: #e74c3c;
}

.empty {
    color: #7f8c8d;
}

.catalog-link {
    display: inline-block;
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #3498db;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    transition: background 0.3s;
}

.catalog-link:hover {
    background: #2980b9;
}

.load-more {
    text-align: center;
    margin-top: 2rem;
}

@media (max-width: 768px) {
    .courses-grid {
        grid-template-columns: 1fr;
    }
}
</style>