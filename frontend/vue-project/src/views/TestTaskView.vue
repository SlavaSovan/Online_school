<template>
    <div class="test-task">
        <div class="test-task__nav">
            <go-back-btn @click="goBack" />
            <h1 class="test-task__title">{{ taskTitle }}</h1>
        </div>

        <div v-if="loading" class="test-task__loading">
            Загрузка теста...
        </div>

        <div v-else-if="error" class="test-task__error">
            <p>{{ error }}</p>
            <base-button @click="loadData">Повторить</base-button>
        </div>

        <div v-else class="test-task__content">
            <!-- Кнопка начала/повторного прохождения теста -->
            <div v-if="!isTakingTest" class="test-start">
                <div class="test-info">
                    <p><strong>Максимальный балл:</strong> {{ maxScore }}</p>
                    <p><strong>Доступно попыток:</strong> {{ remainingAttempts === 0 ? 'Нет' : remainingAttempts }}</p>
                </div>
                <base-button 
                    variant="primary" 
                    @click="startTest"
                    :disabled="!canTakeTest"
                >
                    {{ lastSubmission ? 'Пройти тест заново' : 'Начать тест' }}
                </base-button>
                <div v-if="!canTakeTest && attemptsExhausted" class="test-exhausted-warning">
                    <i class="fas fa-lock"></i>
                    <p>Вы исчерпали все попытки прохождения теста</p>
                </div>
            </div>

            <!-- Форма теста (показывается только когда активен) -->
            <div v-else class="test-form">
                <div class="questions-section">
                    <div
                        v-for="(question, idx) in questions"
                        :key="question.id"
                        class="question-card"
                    >
                        <div class="question-header">
                            <span class="question-number">Вопрос {{ idx + 1 }}</span>
                            <badge variant="primary" :label="getQuestionTypeLabel(question.question_type)" />
                        </div>
                        <div class="question-text">{{ question.text }}</div>
                        
                        <!-- Одиночный выбор -->
                        <div v-if="question.question_type === 'single_choice'" class="options-list">
                            <label v-for="option in question.options" :key="option.id" class="option-radio">
                                <input
                                    type="radio"
                                    :name="`question_${question.id}`"
                                    :value="option.id"
                                    v-model="answers[question.id]"
                                />
                                <span>{{ option.text }}</span>
                            </label>
                        </div>
                        
                        <!-- Множественный выбор -->
                        <div v-else-if="question.question_type === 'multiple_choice'" class="options-list">
                            <label v-for="option in question.options" :key="option.id" class="option-checkbox">
                                <input
                                    type="checkbox"
                                    :value="option.id"
                                    :checked="isOptionSelected(question.id, option.id)"
                                    @change="toggleMultipleChoiceAnswer(question.id, option.id)"
                                />
                                <span>{{ option.text }}</span>
                            </label>
                        </div>
                        
                        <!-- Короткий ответ -->
                        <div v-else-if="question.question_type === 'short_answer'" class="short-answer">
                            <base-input
                                v-model="answers[question.id]"
                                type="text"
                                placeholder="Введите ответ"
                            />
                        </div>
                    </div>
                </div>

                <div class="test-actions">
                    <base-button variant="secondary" @click="cancelTest">Отмена</base-button>
                    <base-button variant="primary" @click="submitTest" :disabled="submitting">
                        {{ submitting ? 'Отправка...' : 'Завершить тест' }}
                    </base-button>
                </div>
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
                    </div>
                </div>
            </div>

            <!-- Детали выбранной попытки -->
            <SubmissionInfo
                v-if="selectedSubmission"
                :submission="selectedSubmission"
                :maxAttempts="maxAttempts"
                :maxScore="maxScore"
                taskType="test"
                @close="closeSubmissionDetails"
            />
        </div>
    </div>
</template>

<script>
import { tasksApi } from '@/api/endpoints/tasks'
import SubmissionInfo from '@/components/SubmissionInfo.vue'

export default {
    name: 'TestTaskView',
    components: { SubmissionInfo },
    data() {
        return {
            questions: [],
            answers: {},
            selectedMultipleAnswers: {},
            submissions: [],
            loading: false,
            submitting: false,
            error: null,
            maxAttempts: 0,
            maxScore: 0,
            taskTitle: '',
            currentSubmissionId: null,
            selectedSubmission: null,
            isTakingTest: false
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
        remainingAttempts() {
            if (this.maxAttempts === 0) return '∞'
            return Math.max(0, this.maxAttempts - this.attemptsUsed)
        },
        canTakeTest() {
            // Можно пройти если не исчерпаны попытки
            return !this.attemptsExhausted
        }
    },
    async mounted() {
        await this.loadData()
    },
    methods: {
        getQuestionTypeLabel(type) {
            const labels = {
                single_choice: 'Одиночный выбор',
                multiple_choice: 'Множественный выбор',
                short_answer: 'Короткий ответ'
            }
            return labels[type] || type
        },
        
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
        
        isOptionSelected(questionId, optionId) {
            const selected = this.selectedMultipleAnswers[questionId]
            return selected ? selected.includes(optionId) : false
        },

        // Переключение выбора варианта
        toggleMultipleChoiceAnswer(questionId, optionId) {
            const currentAnswers = this.selectedMultipleAnswers[questionId] || []
            let newAnswers
            
            if (currentAnswers.includes(optionId)) {
                newAnswers = currentAnswers.filter(id => id !== optionId)
            } else {
                newAnswers = [...currentAnswers, optionId]
            }
            
            // Просто присваиваем новое значение
            this.selectedMultipleAnswers = {
                ...this.selectedMultipleAnswers,
                [questionId]: newAnswers
            }
            this.answers = {
                ...this.answers,
                [questionId]: newAnswers
            }
        },
        
        startTest() {
            // Сбрасываем ответы
            const newAnswers = {}
            const newSelectedMultipleAnswers = {}
            
            this.questions.forEach(q => {
                if (q.question_type === 'multiple_choice') {
                    newSelectedMultipleAnswers[q.id] = []
                    newAnswers[q.id] = []
                } else if (q.question_type === 'single_choice') {
                    newAnswers[q.id] = null
                } else {
                    newAnswers[q.id] = ''
                }
            })
            
            this.answers = newAnswers
            this.selectedMultipleAnswers = newSelectedMultipleAnswers
            this.isTakingTest = true
        },
        
        cancelTest() {
            this.isTakingTest = false
        },
        
        async loadData() {
            this.loading = true
            this.error = null
            
            try {
                const [state, questions, submissions] = await Promise.all([
                    tasksApi.getTaskState(this.taskId),
                    tasksApi.getTestQuestions(this.taskId),
                    tasksApi.getTaskSubmissions(this.taskId)
                ])
                
                this.questions = questions.sort((a, b) => a.order - b.order)
                this.maxAttempts = state.max_attempts
                this.maxScore = state.max_score
                this.submissions = submissions || []
                this.taskTitle = this.$route.query.title || 'Тест'
                
                // Инициализируем структуру для ответов
                const initialAnswers = {}
                const initialMultipleAnswers = {}
                
                this.questions.forEach(q => {
                    if (q.question_type === 'multiple_choice') {
                        initialMultipleAnswers[q.id] = []
                        initialAnswers[q.id] = []
                    } else if (q.question_type === 'single_choice') {
                        initialAnswers[q.id] = null
                    } else {
                        initialAnswers[q.id] = ''
                    }
                })
                
                this.answers = initialAnswers
                this.selectedMultipleAnswers = initialMultipleAnswers
            } catch (err) {
                console.error('Failed to load test:', err)
                this.error = 'Не удалось загрузить тест'
            } finally {
                this.loading = false
            }
        },
        
        async submitTest() {
            // Валидация
            for (const question of this.questions) {
                const answer = this.answers[question.id]
                if (!answer || (Array.isArray(answer) && answer.length === 0)) {
                    this.$toast.warning('Ответьте на все вопросы')
                    return
                }
            }
            
            this.submitting = true
            
            try {
                const formattedAnswers = {}
                for (const question of this.questions) {
                    let answer = this.answers[question.id]
                    if (!Array.isArray(answer)) {
                        answer = [String(answer)]
                    } else {
                        answer = answer.map(a => String(a))
                    }
                    formattedAnswers[question.id] = answer
                }
                
                await tasksApi.submitTest(this.taskId, formattedAnswers)
                this.$toast.success('Тест завершен')
                this.isTakingTest = false
                await this.loadData()
            } catch (err) {
                console.error('Failed to submit test:', err)
                this.$toast.error('Ошибка при отправке теста')
            } finally {
                this.submitting = false
            }
        },
        
        async viewSubmission(submission) {
            if (this.currentSubmissionId === submission.id) {
                // Если уже открыта эта попытка - закрываем её
                this.selectedSubmission = null
                this.currentSubmissionId = null
            } else {
                // Используем уже загруженные данные о попытке
                this.selectedSubmission = submission
                this.currentSubmissionId = submission.id
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
        }
    }
}
</script>

<style scoped>
.test-task {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.test-task__nav {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.test-task__title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 0;
}

.test-task__loading,
.test-task__error {
    text-align: center;
    padding: 3rem;
}

.test-task__error {
    color: #e74c3c;
}

.test-start {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.test-info {
    margin-bottom: 1.5rem;
}

.test-info p {
    margin: 0.5rem 0;
}

.test-passed-info {
    color: #27ae60;
}

.test-exhausted-warning {
    margin-top: 1rem;
    color: #e74c3c;
}

.test-exhausted-warning i {
    font-size: 1.5rem;
}

.questions-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.question-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e9ecef;
}

.question-number {
    font-weight: bold;
    color: #3498db;
}

.question-text {
    font-size: 1.1rem;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.options-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.option-radio,
.option-checkbox {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: background 0.2s;
}

.option-radio:hover,
.option-checkbox:hover {
    background: #f8f9fa;
}

.short-answer {
    margin-top: 1rem;
}

.test-actions {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
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
}
</style>