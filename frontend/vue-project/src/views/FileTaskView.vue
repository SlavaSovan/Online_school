<template>
    <div class="file-task">
        <div class="file-task__nav">
            <go-back-btn @click="goBack" />
            <h1 class="file-task__title">{{ taskTitle }}</h1>
        </div>

        <div v-if="loading" class="file-task__loading">
            Загрузка...
        </div>

        <div v-else-if="error" class="file-task__error">
            <p>{{ error }}</p>
            <base-button @click="loadData">Повторить</base-button>
        </div>

        <div v-else class="file-task__content">
            <!-- Описание задания -->
            <div class="task-description">
                <h3>Описание задания</h3>
                <p>{{ description || 'Нет описания' }}</p>
            </div>

            <!-- Форма загрузки файла (только если можно отправить) -->
            <div v-if="canSubmit" class="upload-section">
                <h3>Загрузить решение</h3>
                <file-upload
                    ref="fileUpload"
                    accept=".pdf,.doc,.docx,.zip,.txt"
                    :uploading="submitting"
                    @file-selected="onFileSelected"
                    @file-cleared="onFileCleared"
                />
                <base-button 
                    variant="primary" 
                    @click="submitFile"
                    :disabled="!selectedFile || submitting"
                    class="submit-btn"
                >
                    {{ submitting ? 'Отправка...' : 'Отправить на проверку' }}
                </base-button>
            </div>

            <!-- Список всех попыток -->
            <div v-if="submissions.length > 0" class="submissions-list">
                <h3 class="submissions-title">История попыток</h3>
                <div class="submissions-items">
                    <div
                        v-for="submission in sortedSubmissions"
                        :key="submission.id"
                        class="submission-item"
                        :class="{ active: currentSubmissionId === submission.id }"
                        @click="viewSubmission(submission)"
                    >
                        <div class="submission-info-row">
                            <span class="attempt-badge">Попытка #{{ submission.attempt }}</span>
                            <badge :variant="getStatusVariant(submission.status)" :label="getStatusLabel(submission.status)" />
                            <span class="submission-date">{{ formatDate(submission.created_at) }}</span>
                        </div>
                        <div class="submission-score">
                            <strong>Балл:</strong> {{ submission.score ?? '-' }} / {{ maxScore }}
                        </div>
                        <div v-if="submission.file_info" class="submission-file">
                            <i class="fas fa-paperclip"></i>
                            {{ submission.file_info.original_filename || 'Файл' }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Детали выбранной попытки -->
            <SubmissionInfo
                v-if="selectedSubmission"
                :submission="selectedSubmission"
                :maxAttempts="maxAttempts"
                :maxScore="maxScore"
                :taskType="'file_upload'"
                :canDelete="canDeleteSelected"
                :on-download="downloadSubmissionFile"
                @delete="deleteSelectedSubmission"
                @close="closeSubmissionDetails"
            />

            <!-- Сообщение, если нет попыток -->
            <div v-if="!loading && submissions.length === 0 && !canSubmit" class="no-submissions">
                <p>У вас пока нет попыток выполнения этого задания</p>
            </div>
        </div>
    </div>
</template>

<script>
import { tasksApi } from '@/api/endpoints/tasks'
import FileUpload from '@/components/UI/FileUpload.vue'
import SubmissionInfo from '@/components/SubmissionInfo.vue'

export default {
    name: 'FileTaskView',
    components: { FileUpload, SubmissionInfo },
    data() {
        return {
            submissions: [],
            loading: false,
            submitting: false,
            error: null,
            maxAttempts: 0,
            maxScore: 0,
            description: '',
            taskTitle: '',
            selectedFile: null,
            currentSubmissionId: null,
            selectedSubmission: null
        }
    },
    computed: {
        taskId() {
            return this.$route.params.taskId
        },
        courseSlug() {
            return this.$route.query.courseSlug
        },
        moduleSlug() {
            return this.$route.query.moduleSlug
        },
        lessonSlug() {
            return this.$route.query.lessonSlug
        },
        sortedSubmissions() {
            return [...this.submissions].sort((a, b) => b.attempt - a.attempt)
        },
        lastSubmission() {
            return this.submissions.length > 0 ? this.submissions[0] : null
        },
        attemptsUsed() {
            return this.submissions.length
        },
        attemptsExhausted() {
            return this.maxAttempts > 0 && this.attemptsUsed >= this.maxAttempts
        },
        canSubmit() {
            // Нельзя отправить, если:
            // 1. Есть последняя попытка со статусом passed (зачтено)
            // 2. Исчерпаны попытки
            if (this.lastSubmission?.status === 'passed') return false
            if (this.attemptsExhausted) return false
            return true
        },
        canDeleteSelected() {
            return this.selectedSubmission && this.selectedSubmission.status === 'needs_review'
        }
    },
    async mounted() {
        await this.loadData()
    },
    methods: {
        getStatusVariant(status) {
            const variants = {
                passed: 'success',
                failed: 'danger',
                needs_review: 'warning',
            }
            return variants[status] || 'info'
        },
        
        getStatusLabel(status) {
            const labels = {
                passed: 'Зачтено',
                failed: 'Не зачтено',
                needs_review: 'На проверке',
            }
            return labels[status] || status
        },

        formatDate(date) {
            if (!date) return 'Не указано'
            return new Date(date).toLocaleString('ru-RU')
        },

        async loadData() {
            this.loading = true
            this.error = null
            
            try {
                const [state, submissions] = await Promise.all([
                    tasksApi.getTaskState(this.taskId),
                    tasksApi.getTaskSubmissions(this.taskId)
                ])
                
                this.maxAttempts = state.max_attempts
                this.maxScore = state.max_score
                this.submissions = submissions || []
                this.taskTitle = this.$route.query.title || 'Задание'
                this.description = this.$route.query.description || ''
                
            } catch (err) {
                console.error('Failed to load task:', err)
                this.error = 'Не удалось загрузить задание'
            } finally {
                this.loading = false
            }
        },
        
        onFileSelected(file) {
            this.selectedFile = file
        },
        
        onFileCleared() {
            this.selectedFile = null
        },
        
        async submitFile() {
            if (!this.selectedFile) {
                this.$toast.warning('Выберите файл')
                return
            }
            
            this.submitting = true
            const formData = new FormData()
            formData.append('file', this.selectedFile)
            
            try {
                await tasksApi.submitFile(this.taskId, formData)
                this.$toast.success('Файл отправлен на проверку')
                this.$refs.fileUpload?.reset()
                this.selectedFile = null
                await this.loadData()
            } catch (err) {
                console.error('Failed to submit file:', err)
                this.$toast.error('Ошибка при отправке файла')
            } finally {
                this.submitting = false
            }
        },
    
        closeSubmissionDetails() {
            this.loadData()
        },
        
        async viewSubmission(submission) {
            if (this.currentSubmissionId === submission.id) {
                this.selectedSubmission = null
                this.currentSubmissionId = null
            } else {
                // Используем уже загруженные данные
                this.selectedSubmission = submission
                this.currentSubmissionId = submission.id
            }
        },
        
        async deleteSelectedSubmission() {
            if (!this.selectedSubmission) return
            
            if (confirm('Удалить эту попытку? Это действие нельзя отменить.')) {
                try {
                    await tasksApi.deleteSubmission(this.taskId, this.selectedSubmission.id)
                    this.$toast.success('Попытка удалена')
                    await this.loadData()
                    this.closeSubmissionDetails()
                } catch (err) {
                    console.error('Failed to delete submission:', err)
                    this.$toast.error('Ошибка при удалении')
                }
            }
        },
        
        closeSubmissionDetails() {
            this.selectedSubmission = null
            this.currentSubmissionId = null
        },
        
        goBack() {
            const courseSlug = this.$route.query.courseSlug
            const moduleSlug = this.$route.query.moduleSlug
            const lessonSlug = this.$route.query.lessonSlug

            this.$router.push(`/course/${courseSlug}/module/${moduleSlug}/lesson/${lessonSlug}`)
        },

        async downloadSubmissionFile(submission) {
            try {
                const response = await tasksApi.downloadSubmission(this.taskId, submission.id)
                const blob = response.data
        
                const filename = submission.file_info?.original_filename || 
                                submission.file_info?.filename || 
                                `submission_${submission.attempt}`
                
                const url = window.URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)
            } catch (err) {
                console.error('Failed to download file:', err)
                this.$toast.error('Ошибка при скачивании файла')
            }
        },
    }
}
</script>

<style scoped>
.file-task {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.file-task__nav {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.file-task__title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 0;
}

.file-task__loading,
.file-task__error {
    text-align: center;
    padding: 3rem;
}

.file-task__error {
    color: #e74c3c;
}

.task-description {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-description h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.upload-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.upload-section h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.submit-btn {
    margin-top: 1rem;
    width: 100%;
}

.submissions-list {
    margin-top: 2rem;
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.submissions-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: #2c3e50;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
}

.submissions-items {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.submission-item {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #e9ecef;
}

.submission-item:hover {
    background: #e9ecef;
    transform: translateX(4px);
}

.submission-item.active {
    background: #e3f2fd;
    border-color: #3498db;
}

.submission-info-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}

.attempt-badge {
    font-weight: bold;
    color: #2c3e50;
}

.submission-date {
    font-size: 0.75rem;
    color: #7f8c8d;
}

.submission-score {
    font-size: 0.875rem;
    color: #6c757d;
    margin-bottom: 0.5rem;
}

.submission-file {
    font-size: 0.75rem;
    color: #3498db;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.submission-file i {
    font-size: 0.75rem;
}

.no-submissions {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    color: #7f8c8d;
}
</style>