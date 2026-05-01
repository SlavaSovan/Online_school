<template>
    <div class="mentor-task">
        <!-- Навигация -->
        <div class="mentor-task__nav">
            <go-back-btn @click="goBack" />
            <h1 class="mentor-task__title">{{ taskTitle }}</h1>
        </div>

        <div v-if="loading" class="mentor-task__loading">
            Загрузка...
        </div>

        <div v-else-if="error" class="mentor-task__error">
            <p>{{ error }}</p>
            <base-button @click="loadData">Повторить</base-button>
        </div>

        <div v-else class="mentor-task__content">
            <!-- Описание задания -->
            <div class="task-description">
                <h3>Описание задания</h3>
                <p>{{ task?.description || 'Нет описания' }}</p>
            </div>

            <!-- Список ответов студентов -->
            <div class="submissions-list">
                <h3 class="submissions-title">Ответы студентов</h3>
                
                <div v-if="submissionsLoading" class="submissions-loading">
                    Загрузка ответов...
                </div>
                
                <div v-else-if="submissions.length === 0" class="no-submissions">
                    <p>Ответов пока нет</p>
                </div>
                
                <div v-else class="submissions-items">
                    <div
                        v-for="submission in sortedSubmissions"
                        :ref="el => { if (submission.id === currentSubmissionId) activeSubmissionRef = el }" 
                        :key="submission.id"
                        class="submission-item"
                        :class="{ active: currentSubmissionId === submission.id }"
                        @click="viewSubmission(submission)"
                    >
                        <div class="submission-info-row">
                            <span class="user-name">{{ getUserDisplayName(submission.user_id) }}</span>
                            <badge :variant="getStatusVariant(submission.status)" :label="getStatusLabel(submission.status)" />
                            <span class="submission-date">{{ formatDate(submission.created_at) }}</span>
                        </div>
                        <div class="submission-score">
                            <strong>Попытка #{{ submission.attempt }}</strong> | 
                            <strong>Балл:</strong> {{ submission.score ?? '-' }} / {{ task?.max_score || '-' }}
                        </div>
                        <div v-if="task?.task_type === 'file' && submission.file_info" class="submission-file">
                            <i class="fas fa-paperclip"></i>
                            {{ submission.file_info.original_filename || 'Файл' }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Детали выбранной попытки -->
            <MentorSubmissionInfo
                v-if="selectedSubmission"
                ref="submissionInfoRef"
                :submission="selectedSubmission"
                :userId="selectedSubmission.user_id"
                :userName="getUserDisplayName(selectedSubmission.user_id)"
                :maxAttempts="task?.max_attempts || 0"
                :maxScore="task?.max_score || 100"
                :taskType="task?.task_type || 'test'"
                :review="currentReview"
                :onDownload="downloadSubmissionFile"
                :onRunCode="runCode"
                :isRunning="running && runningForSubmission === selectedSubmission.id"
                :runOutput="runOutput"
                :runError="runError"
                :wasRun="wasRun"
                @close="closeSubmissionDetails"
                @review="openReviewModal"
                @clear-output="clearRunOutput"
                @delete-review="deleteReview"
            />
        </div>

        <!-- Модальное окно для оценки -->
        <Modal
            :visible="showReviewModal"
            :title="`Оценка ответа пользователя`"
            confirm-text="Сохранить оценку"
            @close="closeReviewModal"
            @confirm="saveReview"
        >
            <div class="review-form">
                <base-input
                    v-model.number="reviewForm.score"
                    label="Оценка"
                    type="number"
                    :placeholder="`0-${task?.max_score || 100}`"
                    required
                />
                <base-input
                    v-model="reviewForm.comment"
                    label="Комментарий"
                    type="textarea"
                    placeholder="Введите комментарий..."
                    :rows="4"
                />
            </div>
        </Modal>
    </div>
</template>

<script>
import { tasksApi } from '@/api/endpoints/tasks'
import { authApi } from '@/api/endpoints/auth'
import Modal from '@/components/Modal.vue'
import MentorSubmissionInfo from '@/components/MentorSubmissionInfo.vue'

export default {
    name: 'MentorTaskView',
    components: { Modal, MentorSubmissionInfo },
    data() {
        return {
            task: null,
            submissions: [],
            loading: false,
            submissionsLoading: false,
            error: null,
            currentSubmissionId: null,
            selectedSubmission: null,
            showReviewModal: false,
            reviewForm: {
                score: 0,
                comment: ''
            },
            // Для запуска кода
            running: false,
            runningForSubmission: null,
            runOutput: '',
            runError: '',
            wasRun: false,
            // Кэш пользователей
            usersCache: {},
            usersLoading: {},
            activeSubmissionRef: null
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
        taskId() {
            return this.$route.params.taskId
        },
        taskTitle() {
            return this.$route.query.title || 'Задание'
        },
        sortedSubmissions() {
            return [...this.submissions].sort((a, b) => b.attempt - a.attempt)
        },
        currentReview() {
            return this.selectedSubmission?.feedback?.review || null
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
                passed: 'Пройдено',
                failed: 'Не пройдено',
                needs_review: 'На проверке',
            }
            return labels[status] || status
        },

        formatDate(date) {
            if (!date) return 'Не указано'
            return new Date(date).toLocaleString('ru-RU')
        },

        getUserDisplayName(userId) {
            const user = this.usersCache[userId]
            if (!user) return `Пользователь #${userId}`
            
            if (user.last_name || user.first_name) {
                const parts = [user.last_name, user.first_name, user.patronymic]
                const fullName = parts.filter(p => p).join(' ')
                if (fullName) return fullName
            }
            return user.email || `Пользователь #${userId}`
        },

        async loadUserInfo(userId) {
            if (this.usersCache[userId]) return this.usersCache[userId]
            if (this.usersLoading[userId]) return
            
            this.usersLoading[userId] = true
            
            try {
                const user = await authApi.getUser(userId)
                this.usersCache[userId] = user
                return user
            } catch (err) {
                console.error(`Failed to load user ${userId}:`, err)
                this.usersCache[userId] = { email: `ID: ${userId}` }
                return this.usersCache[userId]
            } finally {
                this.usersLoading[userId] = false
            }
        },

        async loadUsersForSubmissions() {
            const uniqueUserIds = [...new Set(this.submissions.map(s => s.user_id))]
            await Promise.all(uniqueUserIds.map(id => this.loadUserInfo(id)))
            for (const userId of uniqueUserIds) {
                await this.loadUserInfo(userId)
            }
        },

        async loadData() {
            this.loading = true
            this.error = null
            
            try {
                // Загружаем информацию о задании
                this.task = await tasksApi.getTask(this.taskId)
                
                // Загружаем ответы
                await this.loadSubmissions()
            } catch (err) {
                console.error('Failed to load task:', err)
                this.error = 'Не удалось загрузить задание'
            } finally {
                this.loading = false
            }
        },
        
        async loadSubmissions() {
            this.submissionsLoading = true
            
            try {
                this.submissions = await tasksApi.getSubmissionsForMentor(this.taskId)
                await this.loadUsersForSubmissions()
            } catch (err) {
                console.error('Failed to load submissions:', err)
                this.$toast.error('Не удалось загрузить ответы')
            } finally {
                this.submissionsLoading = false
            }
        },
        
        async viewSubmission(submission) {
            if (this.currentSubmissionId === submission.id) {
                this.selectedSubmission = null
                this.currentSubmissionId = null
                this.selectedReview = null
            } else {
                this.selectedSubmission = submission
                this.currentSubmissionId = submission.id

                await this.$nextTick()
                this.scrollToSubmissionInfo()
            }
        },

        scrollToSubmissionInfo() {
            this.$nextTick(() => {
                const element = this.$refs.submissionInfoRef
                if (element && element.$el) {
                    element.$el.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    })
                }
            })
        },

        scrollToSubmissionItem() {
            this.$nextTick(() => {
                if (this.activeSubmissionRef && this.activeSubmissionRef.scrollIntoView) {
                    this.activeSubmissionRef.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    })
                }
            })
        },
        
        closeSubmissionDetails() {
            this.selectedSubmission = null
            this.currentSubmissionId = null
            this.selectedReview = null
            this.scrollToSubmissionItem()
        },

        async deleteReview(submission) {
            if (!confirm('Удалить оценку? Это действие нельзя отменить.')) return
            
            try {
                await tasksApi.deleteReview(this.taskId, submission.id)
                this.$toast.success('Оценка удалена')
                
                await this.loadSubmissions()
                
                const updatedSubmission = this.submissions.find(s => s.id === submission.id)
                if (updatedSubmission) {
                    this.selectedSubmission = updatedSubmission
                }
            } catch (err) {
                console.error('Failed to delete review:', err)
                this.$toast.error('Ошибка при удалении оценки')
            }
        },
        
        downloadSubmissionFile(submission) {
            if (submission.file_info?.url) {
                window.open(submission.file_info.url, '_blank')
            }
        },
        
        // Запуск кода (для sandbox)
        async runCode(submission) {
            if (!submission.code) {
                this.$toast.warning('Нет кода для выполнения')
                return
            }
            
            this.running = true
            this.runningForSubmission = submission.id
            this.runOutput = ''
            this.runError = ''
            this.wasRun = false
            
            try {
                const result = await tasksApi.runSandbox(this.taskId, submission.code)
                this.wasRun = true
                
                if (result.success) {
                    this.runOutput = result.output || ''
                    this.runError = ''
                } else {
                    this.runError = result.error || 'Ошибка выполнения'
                    this.runOutput = ''
                }
            } catch (err) {
                console.error('Failed to run code:', err)
                this.wasRun = true
                this.runError = 'Не удалось выполнить код'
                this.runOutput = ''
            } finally {
                this.running = false
                this.runningForSubmission = null
            }
        },
        
        clearRunOutput() {
            this.runOutput = ''
            this.runError = ''
            this.wasRun = false
        },
        
        openReviewModal() {
            const review = this.currentReview
            this.reviewForm.score = this.selectedSubmission?.score ?? 0
            this.reviewForm.comment = review?.comment || ''
            this.showReviewModal = true
        },
        
        closeReviewModal() {
            this.showReviewModal = false
            this.reviewForm = { score: 0, comment: '' }
        },
        
        async saveReview() {
            if (!this.selectedSubmission) return
            
            const maxScore = this.task?.max_score || 100
            if (this.reviewForm.score > maxScore) {
                this.$toast.error(`Оценка не может превышать ${maxScore}`)
                return
            }
            
            try {
                const data = {
                    score: this.reviewForm.score,
                    comment: this.reviewForm.comment
                }
                
                if (this.currentReview) {
                    await tasksApi.updateReview(this.taskId, this.selectedSubmission.id, data)
                    this.$toast.success('Оценка обновлена')
                } else {
                    await tasksApi.createReview(this.taskId, this.selectedSubmission.id, data)
                    this.$toast.success('Оценка сохранена')
                }
                
                // Обновляем данные
                await this.loadSubmissions()

                const updatedSubmission = this.submissions.find(s => s.id === this.selectedSubmission.id)
                if (updatedSubmission) {
                    this.selectedSubmission = updatedSubmission
                    await this.$nextTick()
                    this.scrollToSubmissionInfo()
                }
        
                this.closeReviewModal()
            } catch (err) {
                console.error('Failed to save review:', err)
                this.$toast.error('Ошибка при сохранении оценки')
            }
        },
        
        goBack() {
            this.$router.push(`/mentoring/course/${this.courseSlug}`)
        }
    }
}
</script>

<style scoped>
.mentor-task {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.mentor-task__nav {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.mentor-task__title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 0;
}

.mentor-task__loading,
.mentor-task__error {
    text-align: center;
    padding: 3rem;
}

.mentor-task__error {
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

.submissions-list {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.submissions-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: #2c3e50;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
}

.submissions-loading,
.no-submissions {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
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

.user-name {
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

.review-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>