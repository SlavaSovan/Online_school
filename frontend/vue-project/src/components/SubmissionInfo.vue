<template>
    <div class="submission-info">
        <div class="submission-info__header">
            <h3>Результаты попытки #{{ submission.attempt }}</h3>
            <div class="submission-info__actions">
                <action-icon v-if="canDelete && !isTest" variant="delete" @click="deleteSubmission" title="Удалить ответ" />
                <action-icon variant="close" @click="close" title="Закрыть" />
            </div>
        </div>
        
        <div class="submission-info__stats">
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
            <h4>Код решения</h4>
            <div class="code-block">
                <pre><code>{{ submission.code }}</code></pre>
            </div>
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

        <div v-if="feedback" class="submission-info__feedback">
            <!-- Для теста -->
            <div v-if="isTest && feedback.details" class="test-feedback">
                <div class="test-summary">
                    <div class="summary-item">
                        <span class="summary-label">Набрано баллов:</span>
                        <span class="summary-value">{{ feedback.total_score }} / {{ feedback.max_score }}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Процент выполнения:</span>
                        <span class="summary-value">{{ feedback.percentage }}%</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Оценка (5-балльная):</span>
                        <span class="summary-value">{{ feedback.grade_5 }}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Сырой балл:</span>
                        <span class="summary-value">{{ feedback.raw_score }} / {{ feedback.questions_count }}</span>
                    </div>
                </div>

                <div class="questions-details">
                    <h4>Детали по вопросам</h4>
                    <div v-for="(question, idx) in feedback.details" :key="question.question_id" class="question-detail">
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

            <!-- Для проверки ментором (file/sandbox) -->
            <div v-if="feedback.review" class="review-info">
                <h4>Отзыв ментора</h4>
                <div class="review-details">
                    <p><strong>Комментарий:</strong> {{ feedback.review.comment || 'Нет комментария' }}</p>
                    <p><strong>Дата проверки:</strong> {{ formatDate(feedback.review.reviewed_at) }}</p>
                </div>
            </div>

            <div v-if="feedback.raw" class="raw-feedback">
                <h4>Дополнительная информация</h4>
                <pre>{{ JSON.stringify(feedback, null, 2) }}</pre>
            </div>
        </div>

        <div v-if="!feedback && !isSandbox && !submission.file_info" class="no-feedback">
            <p>Нет дополнительной информации о проверке</p>
        </div>
    </div>
</template>

<script>
export default {
    name: 'SubmissionInfo',
    props: {
        submission: {
            type: Object,
            required: true
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
        canDelete: {
            type: Boolean,
            default: false
        },
        onDownload: {
            type: Function,
            default: null
        }
    },
    computed: {
        feedback() {
            return this.submission?.feedback || null
        },
        isTest() {
            return this.taskType === 'test'
        },
        isFile() {
            return this.taskType === 'file_upload'
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

        deleteSubmission() {
            this.$emit('delete')
        },
        
        close() {
            this.$emit('close')
        },

        handleDownload() {
            if (this.onDownload) {
                this.onDownload(this.submission)
            }
        }
    },
    emits: ['delete', 'close']
}
</script>

<style scoped>
.submission-info {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e9ecef;
}

.submission-info__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
}

.submission-info__header h3 {
    margin: 0;
    font-size: 1.25rem;
    color: #2c3e50;
}

.submission-info__stats {
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

.submission-code-detail h4 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #2c3e50;
}

.code-block {
    background: #1e1e1e;
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
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

.code-block code {
    font-family: inherit;
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
    margin-bottom: 1rem;
}

.review-info h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: #2c3e50;
}

.review-details p {
    margin: 0.25rem 0;
}

.raw-feedback {
    margin-top: 1rem;
}

.raw-feedback h4 {
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
    color: #7f8c8d;
}

.raw-feedback pre {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.75rem;
    margin: 0;
}

.no-feedback {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}
</style>