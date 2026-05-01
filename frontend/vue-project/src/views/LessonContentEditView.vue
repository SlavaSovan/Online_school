<template>
    <div class="content-edit">
        <!-- Навигация -->
        <div class="content-edit__nav">
            <go-back-btn @click="goBack" />
            <div class="nav-info">
                <span class="nav-module">{{ moduleTitle }}</span>
                <span class="nav-separator">→</span>
                <span class="nav-lesson">{{ lessonTitle }}</span>
            </div>
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="content-edit__loading">
            Загрузка контента...
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="content-edit__error">
            <p>{{ error }}</p>
            <base-button @click="loadContent">Повторить</base-button>
        </div>

        <!-- Контент -->
        <div v-else class="content-edit__content">
            <div 
                v-for="(item, index) in sortedContent" 
                :key="item.id"
                class="content-item-wrapper"
                draggable="true"
                @dragstart="onDragStart($event, index)"
                @dragover.prevent
                @drop="onDrop($event, index)"
            >
                <div class="drag-handle">⋮⋮</div>
                
                <div class="content-item">
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
                
                <div class="content-actions">
                    <action-icon variant="replace" @click="replaceContent(item)" title="Заменить файл" />
                    <action-icon variant="delete" @click="confirmDelete(item)" title="Удалить" />
                </div>
            </div>
            
            <div v-if="sortedContent.length === 0" class="content-edit__empty">
                <p>В этом уроке пока нет контента</p>
                <p class="empty-hint">Загрузите первый файл с помощью формы ниже</p>
            </div>
        </div>

        <!-- Форма добавления контента -->
        <div class="add-content-section">
            <h3 class="add-content__title">Добавить контент</h3>
            <div class="add-content__form">
                <file-upload
                    ref="fileUpload"
                    :uploading="uploading"
                    :error="uploadError"
                    @file-selected="onFileSelected"
                    @file-cleared="onFileCleared"
                    @update:error="uploadError = $event"
                />
                <base-button 
                    variant="primary" 
                    @click="uploadContent"
                    :disabled="!selectedFile || uploading"
                >
                    <i class="fas fa-upload"></i>
                    {{ uploading ? 'Загрузка...' : 'Загрузить' }}
                </base-button>
            </div>
        </div>

        <Modal
            :visible="showReplaceModal"
            title="Заменить файл"
            confirm-text="Заменить"
            @close="closeReplaceModal"
            @confirm="updateContent"
        >
            <p>Выберите новый файл для замены:</p>
            <file-upload
                ref="replaceFileUpload"
                :uploading="replaceUploading"
                @file-selected="onReplaceFileSelected"
                @file-cleared="onReplaceFileCleared"
            />
        </Modal>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import ContentMarkdown from '@/components/content/ContentMarkdown.vue'
import ContentImage from '@/components/content/ContentImage.vue'
import ContentVideo from '@/components/content/ContentVideo.vue'
import ContentFile from '@/components/content/ContentFile.vue'
import Modal from '@/components/Modal.vue'

export default {
    name: 'LessonContentEditView',
    components: {
        ContentMarkdown,
        ContentImage,
        ContentVideo,
        ContentFile,
        Modal,
    },
    data() {
        return {
            content: [],
            loading: false,
            error: null,
            markdownContents: {},
            selectedFile: null,
            uploading: false,
            uploadError: '',
            dragStartIndex: null,
            showReplaceModal: false,
            replaceContentId: null,
            replaceFile: null,
            replaceUploading: false
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
        moduleTitle() {
            return this.$route.query.moduleTitle || ''
        },
        lessonTitle() {
            return this.$route.query.lessonTitle || ''
        },
        sortedContent() {
            return [...this.content].sort((a, b) => a.order - b.order)
        }
    },
    async mounted() {
        await this.loadContent()
    },
    methods: {
        async loadContent() {
            if (!this.courseSlug || !this.moduleSlug || !this.lessonSlug) {
                this.error = 'Неверные параметры'
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
                console.error('Failed to load content:', err)
                this.error = 'Не удалось загрузить содержимое'
            } finally {
                this.loading = false
            }
        },
        
        onFileSelected(file) {
            this.selectedFile = file
            this.uploadError = ''
        },
        
        onFileCleared() {
            this.selectedFile = null
        },
        
        async uploadContent() {
            if (!this.selectedFile) return
            
            this.uploading = true
            const formData = new FormData()
            formData.append('file', this.selectedFile)
            formData.append('order', this.content.length + 1)
            
            try {
                await coursesApi.uploadContent(
                    this.courseSlug,
                    this.moduleSlug,
                    this.lessonSlug,
                    formData
                )
                await this.loadContent()
                this.$refs.fileUpload?.reset()
                this.selectedFile = null
                this.$toast.success('Контент загружен')
            } catch (err) {
                console.error('Failed to upload content:', err)
                this.uploadError = err.response?.data?.detail || 'Ошибка загрузки файла'
                this.$toast.error(this.uploadError)
            } finally {
                this.uploading = false
            }
        },
        
        replaceContent(item) {
            this.replaceContentId = item.id
            this.replaceFile = null
            this.showReplaceModal = true
        },
        
        onReplaceFileSelected(file) {
            this.replaceFile = file
        },
        
        onReplaceFileCleared() {
            this.replaceFile = null
        },
        
        async updateContent() {
            if (!this.replaceFile) return
            
            this.replaceUploading = true
            const formData = new FormData()
            formData.append('file', this.replaceFile)
            
            try {
                await coursesApi.updateContent(
                    this.courseSlug,
                    this.moduleSlug,
                    this.lessonSlug,
                    this.replaceContentId,
                    formData
                )
                await this.loadContent()
                this.closeReplaceModal()
                this.$toast.success('Файл заменен')
            } catch (err) {
                console.error('Failed to update content:', err)
                this.$toast.error('Ошибка замены')
            } finally {
                this.replaceUploading = false
            }
        },
        
        closeReplaceModal() {
            this.showReplaceModal = false
            this.replaceContentId = null
            this.replaceFile = null
            this.$refs.replaceFileUpload?.reset()
        },
        
        async confirmDelete(item) {
            if (confirm(`Удалить "${item.original_filename}"?`)) {
                try {
                    await coursesApi.deleteContent(
                        this.courseSlug,
                        this.moduleSlug,
                        this.lessonSlug,
                        item.id
                    )
                    await this.loadContent()
                    this.$toast.success('Контент удален')
                } catch (err) {
                    console.error('Failed to delete content:', err)
                    this.$toast.error('Ошибка удаления')
                }
            }
        },
        
        // Drag and drop для переупорядочивания
        onDragStart(event, index) {
            this.dragStartIndex = index
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', index)
        },
        
        async onDrop(event, targetIndex) {
            event.preventDefault()
            
            if (this.dragStartIndex !== null && this.dragStartIndex !== targetIndex) {
                const newContent = [...this.sortedContent]
                const [movedItem] = newContent.splice(this.dragStartIndex, 1)
                newContent.splice(targetIndex, 0, movedItem)
                
                // Обновляем порядок
                const updates = newContent.map((item, idx) => ({
                    id: item.id,
                    order: idx + 1
                }))
                
                // Обновляем локально
                this.content = newContent.map((item, idx) => ({
                    ...item,
                    order: idx + 1
                }))
                
                // Сохраняем порядок на сервере
                try {
                    for (const update of updates) {
                        const formData = new FormData()
                        formData.append('order', update.order)
                        await coursesApi.updateContent(
                            this.courseSlug,
                            this.moduleSlug,
                            this.lessonSlug,
                            update.id,
                            formData
                        )
                    }
                    this.$toast.success('Порядок контента обновлен')
                } catch (err) {
                    console.error('Failed to update order:', err)
                    await this.loadContent()
                    this.$toast.error('Ошибка сохранения порядка')
                }
            }
            
            this.dragStartIndex = null
        },
        
        goBack() {
            this.$router.push(`/course/${this.courseSlug}/edit`)
        }
    }
}
</script>

<style scoped>
.content-edit {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.content-edit__nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
    flex-wrap: wrap;
    gap: 1rem;
}

.nav-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #7f8c8d;
    font-size: 0.875rem;
}

.nav-module {
    color: #2c3e50;
    font-weight: 500;
}

.nav-separator {
    color: #bdc3c7;
}

.nav-lesson {
    color: #3498db;
}

.content-edit__loading,
.content-edit__error,
.content-edit__empty {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    margin-bottom: 2rem;
}

.content-edit__error {
    color: #e74c3c;
}

.content-edit__empty {
    color: #7f8c8d;
}

.empty-hint {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    opacity: 0.7;
}

.content-edit__content {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.content-item-wrapper {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #e9ecef;
    cursor: grab;
}

.content-item-wrapper:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.content-item-wrapper:active {
    cursor: grabbing;
}

.drag-handle {
    cursor: grab;
    color: #bdc3c7;
    font-size: 1.2rem;
    user-select: none;
    padding-top: 0.5rem;
}

.drag-handle:active {
    cursor: grabbing;
}

.content-item {
    flex: 1;
    min-width: 0;
}

.content-actions {
    display: flex;
    gap: 0.5rem;
    padding-top: 0.5rem;
}

.add-content-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.add-content__title {
    font-size: 1.125rem;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.add-content__form {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.add-content__form .btn i {
    margin-right: 0.5rem;
}

@media (max-width: 768px) {
    .content-edit__nav {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .add-content__form {
        flex-direction: column;
    }
    
    .add-content__form .btn {
        width: 100%;
    }
    
    .content-item-wrapper {
        flex-direction: column;
    }
    
    .drag-handle {
        align-self: center;
    }
    
    .content-actions {
        align-self: flex-end;
    }
}
</style>