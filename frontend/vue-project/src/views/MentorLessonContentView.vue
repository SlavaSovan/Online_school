<template>
    <div class="mentor-lesson-content">
        <!-- Навигация -->
        <div class="mentor-lesson-content__nav">
            <go-back-btn @click="goBack" />
            <h1 class="lesson-title">{{ lessonTitle }}</h1>
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="mentor-lesson-content__loading">
            Загрузка контента...
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="mentor-lesson-content__error">
            <p>{{ error }}</p>
            <base-button @click="loadContent">Повторить</base-button>
        </div>

        <!-- Контент -->
        <div v-else class="mentor-lesson-content__content">
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
            
            <div v-if="sortedContent.length === 0" class="mentor-lesson-content__empty">
                <p>В этом уроке пока нет контента</p>
            </div>
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import ContentMarkdown from '@/components/content/ContentMarkdown.vue'
import ContentImage from '@/components/content/ContentImage.vue'
import ContentVideo from '@/components/content/ContentVideo.vue'
import ContentFile from '@/components/content/ContentFile.vue'

export default {
    name: 'MentorLessonContentView',
    components: {
        ContentMarkdown,
        ContentImage,
        ContentVideo,
        ContentFile
    },
    data() {
        return {
            content: [],
            loading: false,
            error: null,
            markdownContents: {}
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
        }
    },
    async mounted() {
        await this.loadContent()
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
            this.$router.push(`/mentoring/course/${this.courseSlug}`)
        }
    }
}
</script>

<style scoped>
.mentor-lesson-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.mentor-lesson-content__nav {
    display: flex;
    align-items: center;
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

.mentor-lesson-content__loading,
.mentor-lesson-content__error,
.mentor-lesson-content__empty {
    text-align: center;
    padding: 3rem;
}

.mentor-lesson-content__error {
    color: #e74c3c;
}

.mentor-lesson-content__empty {
    color: #7f8c8d;
}

.mentor-lesson-content__content {
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
</style>