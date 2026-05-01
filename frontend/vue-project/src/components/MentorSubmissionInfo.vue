<template>
    <div class="mentor-submission-info">
        <div class="mentor-submission-info__header">
            <div class="user-info">
                <h3>{{ userName || `Пользователь #${userId}` }}</h3>
            </div>
            <div class="mentor-submission-info__actions">
                <action-icon variant="close" @click="close" title="Закрыть" />
            </div>
        </div>
        
        <div class="mentor-submission-info__stats">
            <div class="stat-item">
                <div class="stat-label">Статус</div>
                <div class="stat-value">
                    <badge :variant="getStatusVariant(submission.status)" :label="getStatusLabel(submission.status)" />
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Попытка</div>
                <div class="stat-value">{{ submission.attempt }} / {{ maxAttempts === 0 ? '∞' : maxAttempts }}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Балл</div>
                <div class="stat-value">{{ submission.score ?? '-' }} / {{ maxScore }}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Дата</div>
                <div class="stat-value">{{ formatDate(submission.created_at) }}</div>
            </div>
        </div>

        <!-- Код решения (для sandbox заданий) -->
        <div v-if="isSandbox && submission.code" class="submission-code-detail">
            <div class="code-block">
                <pre><code>{{ submission.code }}</code></pre>
            </div>

            <div class="section-header">
                <base-button 
                    v-if="onRunCode" 
                    variant="primary" 
                    size="small" 
                    @click="handleRunCode"
                    :disabled="isRunning"
                >
                    <i class="fas fa-play"></i>
                    {{ isRunning ? 'Выполнение...' : 'Запустить код' }}
                </base-button>
            </div>
            
            <!-- Вывод выполнения кода -->
            <TerminalOutput
                :output="runOutput"
                :error="runError"
                :wasRun="wasRun"
                :loading="isRunning"
                @clear="clearRunOutput"
            />
        </div>

        <!-- Прикрепленный файл (для file заданий) -->
        <div v-if="isFile && submission.file_info" class="submission-file-detail">
            <h4>Прикрепленный файл</h4>
            <div class="file-attachment">
                <i class="fas fa-paperclip"></i>
                <span>{{ submission.file_info.original_filename || 'Файл' }}</span>
                <base-button variant="primary" size="small" @click="handleDownload">
                    Скачать
                </base-button>
            </div>
        </div>

        <!-- Результаты теста -->
        <div v-if="isTest && submission.feedback" class="test-feedback">
                <div class="test-summary">
                    <div class="summary-item">
                        <span class="summary-label">Набрано баллов:</span>
                        <span class="summary-value">{{ submission.feedback.total_score }} / {{ submission.feedback.max_score }}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Процент выполнения:</span>
                        <span class="summary-value">{{ submission.feedback.percentage }}%</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Оценка (5-балльная):</span>
                        <span class="summary-value">{{ submission.feedback.grade_5 }}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Сырой балл:</span>
                        <span class="summary-value">{{ submission.feedback.raw_score }} / {{ submission.feedback.questions_count }}</span>
                    </div>
                </div>

                <div class="questions-details">
                    <h4>Детали по вопросам</h4>
                    <div v-for="(question, idx) in submission.feedback.details" :key="question.question_id" class="question-detail">
                        <div class="question-header">
                            <span class="question-number">{{ idx + 1 }}.</span>
                            <span class="question-text">{{ question.question_text }}</span>
                            <badge 
                                :variant="question.score === question.max_score ? 'success' : 'danger'" 
                                :label="`${question.score} / ${question.max_score}`" 
                            />
                        </div>
                        <div class="question-answer">
                            <strong>Ваш ответ:</strong> {{ formatUserAnswer(question) }}
                        </div>
                        <div v-if="question.correct_answers && question.correct_answers.length > 0" class="question-correct">
                            <strong>Правильный ответ:</strong> 
                            {{ formatCorrectAnswers(question) }}
                        </div>
                    </div>
                </div>
        </div>

        <!-- Отзыв ментора -->
        <div class="review-info">
            <div class="review-header">
                <h4>Отзыв ментора</h4>
                <div class="review-actions">
                    <template v-if="!review">
                        <action-icon variant="add" @click="openReview" title="Добавить отзыв" />
                    </template>
                    <template v-else>
                        <action-icon variant="edit" @click="openReview" title="Изменить отзыв" />
                        <action-icon variant="delete" @click="deleteReview" title="Удалить отзыв" />
                    </template>
                </div>
            </div>
            <div v-if="review" class="review-details">
                <p><strong>Комментарий:</strong> {{ review.comment || 'Нет комментария' }}</p>
                <p><strong>Оценка:</strong> {{ submission.score }} / {{ maxScore }}</p>
                <p><strong>Дата проверки:</strong> {{ formatDate(review.reviewed_at) }}</p>
            </div>
            <div v-else class="review-details empty-review">
                <p class="text-muted">Отзыв еще не добавлен</p>
            </div>
        </div>

        <div v-if="!review && !isTest && !submission.file_info && !(isSandbox && submission.code)" class="no-feedback">
            <p>Нет дополнительной информации о проверке</p>
        </div>
    </div>
</template>

<script>
import TerminalOutput from '@/components/TerminalOutput.vue'

export default {
    name: 'MentorSubmissionInfo',
    components: { TerminalOutput },
    props: {
        submission: {
            type: Object,
            required: true
        },
        userId: {
            type: Number,
            required: true
        },
        userName: {
            type: String,
            default: ''
        },
        maxAttempts: {
            type: Number,
            default: 0
        },
        maxScore: {
            type: Number,
            default: 100
        },
        taskType: {
            type: String,
            default: 'test'
        },
        review: {
            type: Object,
            default: null
        },
        onDownload: {
            type: Function,
            default: null
        },
        onRunCode: {
            type: Function,
            default: null
        },
        isRunning: {
            type: Boolean,
            default: false
        },
        runOutput: {
            type: String,
            default: ''
        },
        runError: {
            type: String,
            default: ''
        },
        wasRun: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isTest() {
            return this.taskType === 'test'
        },
        isFile() {
            return this.taskType === 'file' || this.taskType === 'file_upload'
        },
        isSandbox() {
            return this.taskType === 'sandbox'
        }
    },
    methods: {
        getStatusVariant(status) {
            const variants = {
                passed: 'success',
                failed: 'danger',
                needs_review: 'warning',
                pending: 'warning'
            }
            return variants[status] || 'info'
        },
        
        getStatusLabel(status) {
            const labels = {
                passed: 'Зачтено',
                failed: 'Не зачтено',
                needs_review: 'На проверке',
                pending: 'Ожидает проверки'
            }
            return labels[status] || status
        },
        
        formatUserAnswer(question) {
            if (!question.user_answer || question.user_answer.length === 0) {
                return 'Нет ответа'
            }
            if (question.question_type === 'short_answer') {
                return question.user_answer[0]
            }
            return question.user_answer.join(', ')
        },

        formatCorrectAnswers(question) {
            if (question.question_type === 'short_answer') {
                return question.correct_answers.join(', ')
            }
            return question.correct_answers.join(', ')
        },
        
        formatDate(date) {
            if (!date) return 'Не указано'
            return new Date(date).toLocaleString('ru-RU')
        },
        
        close() {
            this.$emit('close')
        },

        handleDownload() {
            if (this.onDownload) {
                this.onDownload(this.submission)
            }
        },

        handleRunCode() {
            if (this.onRunCode) {
                this.onRunCode(this.submission)
            }
        },

        clearRunOutput() {
            this.$emit('clear-output')
        },

        openReview() {
            this.$emit('review', this.submission)
        },
    
        deleteReview() {
            this.$emit('delete-review', this.submission)
        },
    },
    emits: ['close', 'review', 'clear-output', 'delete-review']
}
</script>

<style scoped>
.mentor-submission-info {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e9ecef;
}

.mentor-submission-info__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
}

.user-info h3 {
    margin: 0;
    font-size: 1.25rem;
    color: #2c3e50;
}

.mentor-submission-info__actions {
    display: flex;
    gap: 0.5rem;
}

.mentor-submission-info__stats {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
    flex-wrap: wrap;
}

.stat-item {
    flex: 1;
    min-width: 100px;
}

.stat-label {
    font-size: 0.75rem;
    color: #7f8c8d;
    margin-bottom: 0.25rem;
}

.stat-value {
    font-weight: bold;
    color: #2c3e50;
}

.submission-code-detail {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.section-header h4 {
    margin: 0;
    font-size: 1rem;
    color: #2c3e50;
}

.code-block {
    background: #1e1e1e;
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
    margin-bottom: 1rem;
}

.code-block pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: #d4d4d4;
    white-space: pre-wrap;
    word-break: break-all;
}

.code-output {
    margin-top: 1rem;
    background: #1a1a2e;
    border-radius: 8px;
    overflow: hidden;
}

.output-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    background: #0d0d1a;
    border-bottom: 1px solid #333;
    font-size: 0.75rem;
    color: #fff;
}

.output-clear {
    background: none;
    border: none;
    color: #fff;
    cursor: pointer;
    font-size: 1.25rem;
}

.output-content {
    padding: 1rem;
    margin: 0;
    font-family: monospace;
    font-size: 0.75rem;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
    background: #1a1a2e;
    color: #00ff00;
}

.output-content.error {
    color: #ff4444;
}

.submission-file-detail {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.submission-file-detail h4 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #2c3e50;
}

.file-attachment {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: #f8f9fa;
    border-radius: 8px;
}

.file-attachment i {
    font-size: 1.25rem;
    color: #3498db;
}

.file-attachment span {
    flex: 1;
    font-size: 0.875rem;
}

.test-summary {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: #e3f2fd;
    border-radius: 8px;
}

.summary-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.summary-label {
    font-size: 0.75rem;
    color: #1565c0;
}

.summary-value {
    font-size: 1.1rem;
    font-weight: bold;
    color: #0d47a1;
}

.questions-details {
    margin-top: 1rem;
}

.questions-details h4 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.question-detail {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 0.75rem;
}

.question-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}

.question-number {
    font-weight: bold;
    color: #3498db;
}

.question-text {
    flex: 1;
    font-weight: 500;
}

.question-answer {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    color: #6c757d;
}

.question-correct {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    color: #27ae60;
}

.review-info {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    margin-top: 1rem;
}

.review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.review-header h4 {
    margin: 0;
    font-size: 1rem;
    color: #2c3e50;
}

.review-actions {
    display: flex;
    gap: 0.5rem;
}

.review-details p {
    margin: 0.25rem 0;
}

.no-feedback {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}
</style>