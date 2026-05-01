<template>
    <div class="tasks-edit">
        <!-- Навигация -->
        <div class="tasks-edit__nav">
            <go-back-btn @click="goBack" />
            <div class="nav-info">
                <span class="nav-module">{{ moduleTitle }}</span>
                <span class="nav-separator">→</span>
                <span class="nav-lesson">{{ lessonTitle }}</span>
            </div>
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="tasks-edit__loading">
            Загрузка заданий...
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="tasks-edit__error">
            <p>{{ error }}</p>
            <base-button @click="loadTasks">Повторить</base-button>
        </div>

        <!-- Список заданий -->
        <div v-else class="tasks-edit__content">
            <div class="tasks-list">
                <TaskItem
                    v-for="(task, index) in sortedTasks"
                    :key="task.id"
                    :task="task"
                    :order="index + 1"
                    :index="index"
                    @drag-start="onDragStart"
                    @drag-end="onDragEnd"
                    @edit="editTask"
                    @delete="confirmDeleteTask"
                />
            </div>
            
            <div v-if="sortedTasks.length === 0" class="tasks-edit__empty">
                <p>В этом уроке пока нет заданий</p>
                <p class="empty-hint">Создайте задание с помощью кнопки ниже</p>
            </div>
        </div>

        <!-- Кнопка добавления задания -->
        <div class="add-task-section">
            <base-button variant="add" class="add-task-btn" @click="openTaskTypeModal">
                + Добавить задание
            </base-button>
        </div>

        <!-- Модальное окно выбора типа задания -->
        <Modal
            :visible="showTaskTypeModal"
            title="Выберите тип задания"
            confirm-text="Далее"
            @close="closeTaskTypeModal"
            @confirm="proceedToTaskForm"
        >
            <div class="task-type-options">
                <div class="task-type-card" :class="{ selected: selectedTaskType === 'test' }" @click="selectedTaskType = 'test'">
                    <div class="task-type-icon">📝</div>
                    <div class="task-type-title">Тест</div>
                    <div class="task-type-desc">Создание вопросов с вариантами ответов</div>
                </div>
                <div class="task-type-card" :class="{ selected: selectedTaskType === 'file' }" @click="selectedTaskType = 'file'">
                    <div class="task-type-icon">📎</div>
                    <div class="task-type-title">Файл</div>
                    <div class="task-type-desc">Загрузка файла с решением</div>
                </div>
                <div class="task-type-card" :class="{ selected: selectedTaskType === 'sandbox' }" @click="selectedTaskType = 'sandbox'">
                    <div class="task-type-icon">💻</div>
                    <div class="task-type-title">Код</div>
                    <div class="task-type-desc">Написание кода на Python</div>
                </div>
            </div>
        </Modal>

        <!-- Модальное окно создания/редактирования задания (базовая форма) -->
        <Modal
            :visible="showTaskFormModal"
            :title="editingTask ? 'Редактирование задания' : `Создание задания (${getTaskTypeLabel(selectedTaskType)})`"
            confirm-text="Сохранить"
            @close="closeTaskFormModal"
            @confirm="saveTask"
        >
            <base-input
                v-model="taskForm.title"
                label="Название задания"
                placeholder="Введите название"
                required
            />
            <base-input
                v-model="taskForm.description"
                label="Описание"
                placeholder="Введите описание"
                type="textarea"
                :rows="4"
            />
            <base-input
                v-model.number="taskForm.max_score"
                label="Максимальный балл"
                type="number"
                placeholder="100"
                required
            />
            <base-input
                v-model.number="taskForm.max_attempts"
                label="Максимальное количество попыток (0 - без ограничений)"
                type="number"
                placeholder="0"
            />
            <base-select
                v-if="selectedTaskType === 'sandbox'"
                v-model="taskForm.language"
                label="Язык программирования"
                :options="languageOptions"
                required
            />
        </Modal>

        <!-- Модальное окно редактирования теста (с вопросами) -->
        <Modal
            :visible="showTestEditorModal"
            :title="`Редактирование теста: ${editingTask?.title}`"
            confirm-text="Сохранить тест"
            class="test-editor-modal"
            @close="closeTestEditorModal"
            @confirm="saveTestWithQuestions"
        >
            <div class="test-editor">
                <div class="questions-section">                    
                    <div v-if="questions.length === 0" class="empty-questions">
                        <p>Вопросы отсутствуют</p>
                    </div>

                    <div v-else class="questions-list">
                        <QuestionEditor
                            v-for="(question, index) in questions"
                            :key="question.tempId || question.id"
                            :question="question"
                            :order="index + 1"
                            :index="index"
                            @delete="deleteQuestion(index)"
                        />
                    </div>
            
                    <base-button 
                        variant="add" 
                        class="add-question-btn"
                        @click="addQuestion"
                    >
                        + Добавить вопрос
                    </base-button>
                </div>
            </div>
        </Modal>
    </div>
</template>

<script>
import { tasksApi } from '@/api/endpoints/tasks'
import Modal from '@/components/Modal.vue'
import TaskItem from '@/components/TaskItem.vue'
import QuestionEditor from '@/components/QuestionEditor.vue'

export default {
    name: 'LessonTasksEditView',
    components: { Modal, TaskItem, QuestionEditor },
    data() {
        return {
            tasks: [],
            loading: false,
            error: null,
            dragStartIndex: null,
            // Тип задания
            showTaskTypeModal: false,
            selectedTaskType: 'test',
            // Форма задания
            showTaskFormModal: false,
            editingTask: null,
            taskForm: {
                title: '',
                description: '',
                max_score: 100,
                max_attempts: 0,
                language: 'python'
            },
            languageOptions: [
                { value: 'python', label: 'Python' }
            ],
            // Редактор теста
            showTestEditorModal: false,
            questions: [],
            tempTaskId: null,
            questionDragStartIndex: null
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
        sortedTasks() {
            return [...this.tasks].sort((a, b) => a.order - b.order)
        }
    },
    async mounted() {
        await this.loadTasks()
    },
    methods: {
        getTaskTypeLabel(type) {
            const labels = {
                test: 'Тест',
                file: 'Файл',
                sandbox: 'Код'
            }
            return labels[type] || type
        },
        
        async loadTasks() {
            if (!this.courseSlug || !this.moduleSlug || !this.lessonSlug) {
                this.error = 'Неверные параметры'
                return
            }
            
            this.loading = true
            this.error = null
            
            try {
                const response = await tasksApi.getLessonTasks(
                    this.courseSlug,
                    this.moduleSlug,
                    this.lessonSlug
                )
                this.tasks = response || []
            } catch (err) {
                console.error('Failed to load tasks:', err)
                this.error = 'Не удалось загрузить задания'
            } finally {
                this.loading = false
            }
        },
        
        // Drag and drop для заданий
        onDragStart(index) {
            this.dragStartIndex = index
        },
        
        async onDragEnd() {
            if (this.dragStartIndex !== null) {
                // Сохраняем новый порядок
                const newTasks = [...this.tasks]
                const [movedItem] = newTasks.splice(this.dragStartIndex, 1)
                newTasks.splice(this.dragStartIndex, 0, movedItem)
                
                // Обновляем порядок
                for (let i = 0; i < newTasks.length; i++) {
                    if (newTasks[i].order !== i + 1) {
                        try {
                            await tasksApi.updateTask(newTasks[i].id, {
                                title: newTasks[i].title,
                                description: newTasks[i].description,
                                order: i + 1,
                                is_active: newTasks[i].is_active,
                                max_attempts: newTasks[i].max_attempts,
                                max_score: newTasks[i].max_score
                            })
                            newTasks[i].order = i + 1
                        } catch (err) {
                            console.error('Failed to update task order:', err)
                        }
                    }
                }
                
                this.tasks = newTasks
                this.dragStartIndex = null
            }
        },
        
        // Выбор типа задания
        openTaskTypeModal() {
            this.selectedTaskType = 'test'
            this.showTaskTypeModal = true
        },
        
        closeTaskTypeModal() {
            this.showTaskTypeModal = false
        },
        
        proceedToTaskForm() {
            this.closeTaskTypeModal()
            this.editingTask = null
            this.taskForm = {
                title: '',
                description: '',
                max_score: 100,
                max_attempts: 0,
                language: 'python'
            }
            this.showTaskFormModal = true
        },
        
        closeTaskFormModal() {
            this.showTaskFormModal = false
        },
        
        // Создание/редактирование задания
        async saveTask() {
            if (!this.taskForm.title) {
                this.$toast.warning('Введите название задания')
                return
            }
            
            const data = {
                title: this.taskForm.title,
                description: this.taskForm.description,
                order: this.tasks.length + 1,
                max_attempts: this.taskForm.max_attempts,
                max_score: this.taskForm.max_score
            }
            
            try {
                let response
                if (this.editingTask) {
                    // Обновление существующего задания
                    response = await tasksApi.updateTask(this.editingTask.id, data)
                    this.$toast.success('Задание обновлено')
                } else {
                    // Создание нового задания
                    switch (this.selectedTaskType) {
                        case 'test':
                            response = await tasksApi.createTestTask(
                                this.courseSlug,
                                this.moduleSlug,
                                this.lessonSlug,
                                data
                            )
                            // После создания теста открываем редактор вопросов
                            this.tempTaskId = response.id
                            this.closeTaskFormModal()
                            await this.loadTasks()
                            await this.openTestEditor(response)
                            return
                        case 'file':
                            response = await tasksApi.createFileTask(
                                this.courseSlug,
                                this.moduleSlug,
                                this.lessonSlug,
                                data
                            )
                            this.$toast.success('Задание создано')
                            break
                        case 'sandbox':
                            response = await tasksApi.createSandboxTask(
                                this.courseSlug,
                                this.moduleSlug,
                                this.lessonSlug,
                                { ...data, language: this.taskForm.language }
                            )
                            this.$toast.success('Задание создано')
                            break
                    }
                }
                
                await this.loadTasks()
                this.closeTaskFormModal()
            } catch (err) {
                console.error('Failed to save task:', err)
                this.$toast.error('Ошибка при сохранении задания')
            }
        },
        
        editTask(task) {
            this.editingTask = task
            this.selectedTaskType = task.task_type
            this.taskForm = {
                title: task.title,
                description: task.description || '',
                max_score: task.max_score,
                max_attempts: task.max_attempts || 0,
                language: task.language || 'python'
            }
            
            if (task.task_type === 'test') {
                this.openTestEditor(task)
            } else {
                this.showTaskFormModal = true
            }
        },
        
        async confirmDeleteTask(task) {
            if (confirm(`Удалить задание "${task.title}"?`)) {
                try {
                    await tasksApi.deleteTask(task.id)
                    await this.loadTasks()
                    this.$toast.success('Задание удалено')
                } catch (err) {
                    console.error('Failed to delete task:', err)
                    this.$toast.error('Ошибка при удалении задания')
                }
            }
        },
        
        // Редактор теста
        async openTestEditor(task) {
            this.editingTask = task
            this.showTestEditorModal = true
            await this.loadQuestions(task.id)
        },
        
        async loadQuestions(taskId) {
            try {
                const response = await tasksApi.getTaskQuestions(taskId)
                this.questions = response.map(q => ({
                    ...q,
                    tempId: Date.now() + Math.random()
                }))
            } catch (err) {
                console.error('Failed to load questions:', err)
                this.questions = []
            }
        },
        
        addQuestion() {
            const newQuestion = {
                tempId: Date.now() + Math.random(),
                text: '',
                question_type: 'single_choice',
                order: this.questions.length + 1,
                options: [{ text: '', is_correct: false }],
                correct_answers: []
            }
            this.questions.push(newQuestion)
        },
        
        deleteQuestion(index) {
            this.questions.splice(index, 1)
            this.questions.forEach((q, idx) => {
                q.order = idx + 1
            })
            this.$toast.success('Вопрос удален')
        },
        
        onQuestionDragStart(index) {
            this.questionDragStartIndex = index
        },
        
        onQuestionDragEnd() {
            if (this.questionDragStartIndex !== null) {
                const [movedItem] = this.questions.splice(this.questionDragStartIndex, 1)
                this.questions.splice(this.questionDragStartIndex, 0, movedItem)
                this.questions.forEach((q, idx) => {
                    q.order = idx + 1
                })
                this.questionDragStartIndex = null
            }
        },
        
        async saveTestWithQuestions() {
            // Валидация
            for (const question of this.questions) {
                if (!question.text.trim()) {
                    this.$toast.warning('Заполните текст всех вопросов')
                    return
                }
                
                if (question.question_type === 'single_choice' || question.question_type === 'multiple_choice') {
                    let hasCorrect = false
                    for (const option of question.options) {
                        if (option.is_correct) hasCorrect = true
                        if (!option.text.trim()) {
                            this.$toast.warning('Заполните текст всех вариантов ответов')
                            return
                        }
                    }
                    if (!hasCorrect) {
                        this.$toast.warning('Отметьте правильный вариант ответа')
                        return
                    }
                }
            }
            
            try {
                // Удаляем старые вопросы и создаем новые
                // Сначала получаем существующие вопросы
                const existingQuestions = await tasksApi.getTaskQuestions(this.editingTask.id)
                
                // Удаляем все старые вопросы
                for (const q of existingQuestions) {
                    await tasksApi.deleteQuestion(this.editingTask.id, q.id)
                }
                
                // Создаем новые вопросы
                for (let i = 0; i < this.questions.length; i++) {
                    const q = this.questions[i]
                    const questionData = {
                        text: q.text,
                        order: i + 1,
                        question_type: q.question_type
                    }
                    
                    if (q.question_type === 'single_choice' || q.question_type === 'multiple_choice') {
                        questionData.options = q.options.map(opt => ({
                            text: opt.text,
                            is_correct: opt.is_correct
                        }))
                    } else if (q.question_type === 'short_answer') {
                        questionData.correct_answers = q.correct_answers || []
                    }
                    
                    await tasksApi.createQuestion(this.editingTask.id, questionData)
                }
                
                this.$toast.success('Тест сохранен')
                this.closeTestEditorModal()
            } catch (err) {
                console.error('Failed to save test:', err)
                this.$toast.error('Ошибка при сохранении теста')
            }
        },
        
        closeTestEditorModal() {
            this.showTestEditorModal = false
            this.editingTask = null
            this.questions = []
        },
        
        goBack() {
            this.$router.push(`/course/${this.courseSlug}/edit`)
        }
    }
}
</script>

<style scoped>
.tasks-edit {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.tasks-edit__nav {
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

.tasks-edit__loading,
.tasks-edit__error,
.tasks-edit__empty {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    margin-bottom: 2rem;
}

.tasks-edit__error {
    color: #e74c3c;
}

.tasks-edit__empty {
    color: #7f8c8d;
}

.empty-hint {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    opacity: 0.7;
}

.tasks-edit__content {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tasks-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.add-task-section {
    text-align: center;
}

.add-task-btn {
    min-width: 200px;
}

/* Выбор типа задания */
.task-type-options {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.task-type-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.task-type-card:hover {
    border-color: #3498db;
    background: #e3f2fd;
}

.task-type-card.selected {
    border-color: #3498db;
    background: #e3f2fd;
}

.task-type-icon {
    font-size: 2rem;
}

.task-type-title {
    font-weight: bold;
    color: #2c3
}

.task-type-desc {
    font-size: 0.875rem;
    color: #7f8c8d;
}

/* Редактор теста */
.test-editor {
    max-height: 70vh;
    overflow-y: auto;
}

.questions-section {
    margin-top: 0;
}

.questions-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.questions-header h4 {
    margin: 0;
    color: #2c3e50;
}

.questions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.empty-questions {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
    background: #f8f9fa;
    border-radius: 8px;
}

.add-question-btn {
    width: 100%;
    margin-top: 1.2rem;
}

:deep(.test-editor-modal .modal) {
    max-width: 900px;
    width: 95%;
}

:deep(.test-editor-modal .modal-body) {
    padding: 1.5rem;
}

/* Заголовок модального окна по центру */
:deep(.test-editor-modal .modal-header) {
    text-align: center;
}

:deep(.test-editor-modal .modal-title) {
    width: 100%;
    text-align: center;
    font-size: 1.35rem;
}

@media (max-width: 768px) {
    .tasks-edit__nav {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .task-type-card {
        flex-direction: column;
        text-align: center;
    }
}
</style>