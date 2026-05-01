<template>
    <div class="question-editor" :class="{ 'question-editor--expanded': isExpanded }">
        <div class="question-header" @click="isExpanded = !isExpanded">
            <div class="drag-handle">⋮⋮</div>
            <div class="question-order">{{ order }}.</div>
            <div class="question-text-preview">{{ question.text || 'Новый вопрос' }}</div>
            <div class="question-type-badge">
                <badge :variant="getQuestionTypeVariant()" :label="getQuestionTypeLabel()" />
            </div>
            <div class="question-actions" @click.stop>
                <action-icon variant="delete" @click="handleDelete" title="Удалить вопрос" />
                <span class="expand-icon">{{ isExpanded ? '▲' : '▼' }}</span>
            </div>
        </div>
        
        <div v-if="isExpanded" class="question-body">
            <base-input
                v-model="question.text"
                label="Текст вопроса"
                placeholder="Введите текст вопроса"
                required
            />
            
            <base-select
                v-model="question.question_type"
                label="Тип вопроса"
                :options="questionTypeOptions"
                required
                @update:modelValue="onQuestionTypeChange"
            />
            
            <!-- Варианты ответов для single_choice и multiple_choice -->
            <div v-if="isChoiceType" class="options-section">
                <div class="options-header">
                    <h4 class="options-title">Варианты ответов</h4>
                </div>
                
                <div class="options-list">
                    <div
                        v-for="(option, idx) in question.options"
                        :key="idx"
                        class="option-item"
                    >
                        <input
                            type="checkbox"
                            v-model="option.is_correct"
                            class="option-correct"
                            :class="{ 'multiple': isMultipleChoice }"
                            @click.stop
                        />
                        <base-input
                            v-model="option.text"
                            :placeholder="`Вариант ${idx + 1}`"
                            class="option-input"
                            @click.stop
                        />
                        <action-icon variant="delete" size="small" @click="removeOption(idx)" title="Удалить вариант" />
                    </div>
                </div>
                
                <base-button 
                    variant="add" 
                    class="add-option-btn"
                    @click="addOption"
                >
                    + Добавить вариант
                </base-button>
                
                <div v-if="isSingleChoice" class="option-hint">
                    <small>Отметьте правильный вариант (только один)</small>
                </div>
                <div v-if="isMultipleChoice" class="option-hint">
                    <small>Отметьте все правильные варианты</small>
                </div>
            </div>
            
            <!-- Короткий ответ -->
            <div v-if="isShortAnswer" class="short-answer-section">
                <base-input
                    v-model="correctAnswersText"
                    label="Правильные ответы"
                    placeholder="Введите правильные ответы через запятую"
                    type="textarea"
                    :rows="3"
                />
                <div class="option-hint">
                    <small>Например: Гречка, греча, гречневая крупа</small>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'QuestionEditor',
    props: {
        question: {
            type: Object,
            required: true
        },
        order: {
            type: Number,
            required: true
        },
        index: {
            type: Number,
            required: true
        }
    },
    data() {
        return {
            isExpanded: true,
            questionTypeOptions: [
                { value: 'single_choice', label: 'Одиночный выбор' },
                { value: 'multiple_choice', label: 'Множественный выбор' },
                { value: 'short_answer', label: 'Короткий ответ' }
            ]
        }
    },
    computed: {
        isChoiceType() {
            return this.question.question_type === 'single_choice' || this.question.question_type === 'multiple_choice'
        },
        isSingleChoice() {
            return this.question.question_type === 'single_choice'
        },
        isMultipleChoice() {
            return this.question.question_type === 'multiple_choice'
        },
        isShortAnswer() {
            return this.question.question_type === 'short_answer'
        },
        correctAnswersText: {
            get() {
                return this.question.correct_answers ? this.question.correct_answers.join(', ') : ''
            },
            set(val) {
                this.question.correct_answers = val.split(',').map(s => s.trim()).filter(s => s)
            }
        }
    },
    methods: {
        getQuestionTypeLabel() {
            const labels = {
                single_choice: 'Одиночный выбор',
                multiple_choice: 'Множественный выбор',
                short_answer: 'Короткий ответ'
            }
            return labels[this.question.question_type] || this.question.question_type
        },
        
        getQuestionTypeVariant() {
            const variants = {
                single_choice: 'primary',
                multiple_choice: 'info',
                short_answer: 'warning'
            }
            return variants[this.question.question_type] || 'secondary'
        },
        
        toggleExpand() {
            this.isExpanded = !this.isExpanded
        },
        
        handleDelete() {
            this.$emit('delete')
        },
        
        onQuestionTypeChange() {
            if (this.isChoiceType) {
                if (!this.question.options || this.question.options.length === 0) {
                    this.question.options = [{ text: '', is_correct: false }]
                }
            } else {
                this.question.options = []
                if (!this.question.correct_answers) {
                    this.question.correct_answers = []
                }
            }
        },
        
        addOption() {
            this.question.options.push({ text: '', is_correct: false })
        },
        
        removeOption(index) {
            this.question.options.splice(index, 1)
            if (this.question.options.length === 0) {
                this.question.options.push({ text: '', is_correct: false })
            }
        }
    },
    mounted() {
        // Инициализация
        if (!this.question.options) {
            this.question.options = []
        }
        if (this.isChoiceType && this.question.options.length === 0) {
            this.question.options = [{ text: '', is_correct: false }]
        }
        if (!this.question.correct_answers) {
            this.question.correct_answers = []
        }
    },
    emits: ['delete']
}
</script>

<style scoped>
.question-editor {
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    overflow: hidden;
    margin-bottom: 1rem;
}

.question-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: #f8f9fa;
    cursor: pointer;
    transition: background 0.2s;
}

.question-header:hover {
    background: #e9ecef;
}

.drag-handle {
    cursor: grab;
    color: #adb5bd;
    font-size: 1.2rem;
    user-select: none;
}

.drag-handle:active {
    cursor: grabbing;
}

.question-order {
    font-weight: bold;
    color: #3498db;
}

.question-text-preview {
    flex: 1;
    font-weight: 500;
    color: #2c3e50;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.question-type-badge {
    margin-left: auto;
}

.question-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.expand-icon {
    color: #7f8c8d;
    font-size: 0.75rem;
}

.question-body {
    padding: 1rem;
    border-top: 1px solid #e9ecef;
    background: white;
}

.options-section {
    margin-top: 1rem;
}

.options-header {
    text-align: center;
    margin-bottom: 1rem;
}

.options-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 400;
    color: #2c3e50;
}

.options-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.option-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.option-correct {
    width: 1.2rem;
    height: 1.2rem;
    cursor: pointer;
    flex-shrink: 0;
}

.option-correct.multiple {
    border-radius: 4px;
}

.option-input {
    flex: 1;
}

.add-option-btn {
    width: 100%;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

.option-hint {
    margin-top: 0.5rem;
    color: #7f8c8d;
}

.short-answer-section {
    margin-top: 1rem;
}
</style>