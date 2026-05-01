<template>
    <div class="course-edit">
        
        <div class="course-edit__nav">
            <go-back-btn @click="goBack" />
        </div>

        <div class="course-edit__header">
            <h1 class="course-edit__title">Редактор курса</h1>
        </div>

        <form @submit.prevent="saveCourse" class="course-form">
            <!-- Основная информация -->
            <div class="form-section">
                <h2 class="form-section__title">Основная информация</h2>
                
                <base-input
                    v-model="form.title"
                    label="Название курса"
                    placeholder="Введите название"
                    required
                />
                
                <base-input
                    v-model="form.description"
                    label="Описание"
                    placeholder="Введите описание"
                    type="textarea"
                />
                
                <base-input
                    v-model="form.price"
                    label="Цена"
                    type="number"
                    placeholder="0.00"
                />
                
                <base-select
                    v-model="form.category"
                    label="Категория"
                    :options="categoryOptions"
                    required
                />
                
                <base-select
                    v-model="form.status"
                    label="Статус"
                    :options="statusOptions"
                    required
                />
            </div>

            <!-- Модули курса -->
            <div class="form-section">
                <h2 class="form-section__title">Модули курса</h2>
                
                <div v-if="modules.length === 0" class="empty-modules">
                    <p>Модули отсутствуют</p>
                </div>
                
                <div v-else class="modules-list">
                    <div
                        v-for="(module, moduleIndex) in modules"
                        :key="module.id"
                        class="module-card"
                        draggable="true"
                        @dragstart="onDragStartModule($event, moduleIndex)"
                        @dragover.prevent
                        @dragenter.prevent
                        @drop="onDropModule($event, moduleIndex)"
                    >
                        <div class="module-header">
                            <div class="drag-handle">⋮⋮</div>
                            <div class="module-info" @click="toggleModule(module.id)">
                                <span class="module-order">{{ module.order }}.</span>
                                <h3 class="module-title">{{ module.title }}</h3>
                                <span class="lesson-count">({{ getLessonsCount(module) }} уроков)</span>
                            </div>
                            <div class="module-actions">
                                <action-icon variant="edit" @click="editModule(module)" title="Редактировать" />
                                <action-icon variant="delete" @click="deleteModule(module)" title="Удалить" />
                            </div>
                        </div>
                        
                        <!-- Уроки внутри модуля -->
                        <div v-if="isModuleExpanded(module.id)" class="lessons-section">
                            
                            <div v-if="getLessonsCount(module) === 0" class="empty-lessons">
                                <p>Уроки отсутствуют</p>
                            </div>
                            
                            <div v-else class="lessons-list">
                                <div
                                    v-for="(lesson, lessonIndex) in module.lessons"
                                    :key="lesson.id"
                                    class="lesson-item"
                                    draggable="true"
                                    @dragstart="onDragStartLesson($event, module.id, lessonIndex)"
                                    @dragover.prevent
                                    @dragenter.prevent
                                    @drop="onDropLesson($event, module.id, lessonIndex)"
                                >
                                    <div class="drag-handle-small">⋮</div>
                                    <div class="lesson-info" @click="editLesson(module, lesson)">
                                        <span class="lesson-order">{{ lesson.order }}.</span>
                                        <span class="lesson-title">{{ lesson.title }}</span>
                                        <div class="lesson-badges">
                                            <badge 
                                                :variant="lesson.is_published ? 'published' : 'draft'"
                                                :label="lesson.is_published ? 'Опубликован' : 'Черновик'"
                                            />
                                            <badge 
                                                v-if="hasLessonContent(lesson)"
                                                variant="content"
                                                label="Контент"
                                            />
                                            <badge 
                                                v-if="hasLessonTasks(lesson)"
                                                variant="tasks"
                                                label="Задания"
                                            />
                                        </div>
                                    </div>
                                    <div class="lesson-actions">
                                        <action-icon variant="content" @click="manageContent(module, lesson)" title="Управление контентом" />
                                        <action-icon variant="tasks" @click="manageTasks(module, lesson)" title="Управление заданиями" />
                                        <action-icon variant="edit" @click="editLesson(module, lesson)" title="Редактировать" />
                                        <action-icon variant="delete" @click="deleteLesson(module, lesson)" title="Удалить" />
                                    </div>
                                </div>
                            </div>

                            <base-button variant="add" class="add-lesson-btn" @click="openLessonModal(module)">+ Добавить урок</base-button>
                        </div>
                    </div>
                </div>
                
                <base-button
                    v-if="courseId"
                    variant="add"
                    class="add-module-btn"
                    @click="openModuleModal(module)"
                >
                    + Добавить модуль
                </base-button>
                <div v-else class="info-hint">
                    Сначала сохраните курс, чтобы добавить модули
                </div>
            </div>
            
            <div class="form-actions">
                <base-button variant="primary" type="submit" :disabled="saving">
                    {{ saving ? 'Сохранение...' : (isEditing ? 'Сохранить' : 'Создать') }}
                </base-button>
                <base-button variant="secondary" @click="goBack">Отмена</base-button>
                <base-button v-if="isEditing" variant="danger" @click="confirmDelete">
                    Удалить
                </base-button>
            </div>
        </form>

        <!-- Модальное окно для модуля -->
        <Modal
            :visible="showModuleModal"
            :title="editingModule ? 'Редактирование модуля' : 'Создание модуля'"
            @close="closeModuleModal"
            @confirm="saveModule"
        >
            <base-input
                v-model="moduleForm.title"
                label="Название модуля"
                placeholder="Введите название"
                required
            />
            <base-input
                v-model="moduleForm.description"
                label="Описание"
                placeholder="Введите описание"
                type="textarea"
            />
        </Modal>

        <!-- Модальное окно для урока -->
        <Modal
            :visible="showLessonModal"
            :title="editingLesson ? 'Редактирование урока' : 'Создание урока'"
            @close="closeLessonModal"
            @confirm="saveLesson"
        >
            <base-input
                v-model="lessonForm.title"
                label="Название урока"
                placeholder="Введите название"
                required
            />
            <base-checkbox
                v-model="lessonForm.is_published"
                label="Опубликован"
            />
        </Modal>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import { categoriesApi } from '@/api/endpoints/categories'
import Modal from '@/components/Modal.vue'

export default {
    name: 'CourseEditView',
    components: { Modal },
    data() {
        return {
            course: null,
            courseId: null,
            modules: [],
            expandedModules: {},
            form: {
                title: '',
                description: '',
                price: '',
                category: null,
                status: 'draft'
            },
            saving: false,
            categories: [],
            statusOptions: [
                { value: 'draft', label: 'Проектируется' },
                { value: 'published', label: 'Опубликован' },
                { value: 'archived', label: 'Архивирован' }
            ],
            // Module modal
            showModuleModal: false,
            editingModule: null,
            moduleForm: {
                title: '',
                description: ''
            },
            // Lesson modal
            showLessonModal: false,
            editingLesson: null,
            currentModuleForLesson: null,
            lessonForm: {
                title: '',
                is_published: false
            },
            // Drag and drop
            dragModuleIndex: null,
            dragLessonData: null
        }
    },
    computed: {
        isEditing() {
            return !!this.$route.params.slug
        },
        courseSlug() {
            return this.$route.params.slug
        },
        categoryOptions() {
            return this.categories.map(cat => ({
                value: cat.id,
                label: cat.name
            }))
        }
    },
    async mounted() {
        await this.loadCategories()
        if (this.isEditing) {
            await this.loadCourse()
        }
    },
    methods: {
        getLessonsCount(module) {
            return module.lessons ? module.lessons.length : 0
        },
    
        hasLessonContent(lesson) {
            return lesson.content && lesson.content.length > 0
        },
        
        hasLessonTasks(lesson) {
            return lesson.tasks && lesson.tasks.length > 0
        },
        
        isModuleExpanded(moduleId) {
            return this.expandedModules[moduleId] !== false
        },
        
        async loadCategories() {
            try {
                const response = await categoriesApi.getCategories()
                this.categories = response.results || []
            } catch (err) {
                console.error('Failed to load categories:', err)
            }
        },
        
        async loadCourse() {
            try {
                const response = await coursesApi.getPrivateCourseBySlug(this.courseSlug)
                
                this.course = response
                this.courseId = response.id
                this.form.title = response.title || ''
                this.form.description = response.description || ''
                this.form.price = response.price || ''
                this.form.category = response.category
                this.form.status = response.status || 'draft'
                
                // Сортируем модули
                const sortedModules = (response.modules || []).sort((a, b) => a.order - b.order)
                
                // Сортируем уроки внутри модулей
                sortedModules.forEach(module => {
                    if (module.lessons && module.lessons.length > 0) {
                        module.lessons.sort((a, b) => a.order - b.order)
                    } else {
                        module.lessons = []
                    }
                })
                
                this.modules = sortedModules
                
                // Инициализируем expandedModules для всех модулей (по умолчанию раскрыты)
                this.modules.forEach(module => {
                    if (this.expandedModules[module.id] === undefined) {
                        this.expandedModules[module.id] = true
                    }
                })
                
            } catch (err) {
                console.error('Failed to load course:', err)
                this.$router.push('/my-courses')
            }
        },
        
        async saveCourse() {
            this.saving = true
            
            try {
                const data = {
                    title: this.form.title,
                    description: this.form.description,
                    price: this.form.price,
                    category: this.form.category,
                    status: this.form.status
                }
                
                if (this.isEditing) {
                    await coursesApi.updateCourse(this.courseSlug, data)
                    await this.saveAllOrders()
                    this.$toast.success('Курс успешно сохранен')
                    await this.loadCourse()
                } else {
                    const response = await coursesApi.createCourse(data)
                    this.$toast.success('Курс создан')
                    this.$router.replace(`/course/${response.slug}/edit`)
                    return
                }
            } catch (err) {
                console.error('Save error:', err)
                this.$toast.error('Ошибка при сохранении курса')
            } finally {
                this.saving = false
            }
        },
        
        // Сохранение порядка всех модулей и уроков
        async saveAllOrders() {
            // Сохраняем порядок модулей
            for (let i = 0; i < this.modules.length; i++) {
                const module = this.modules[i]
                const newOrder = i + 1
        
                try {
                    await coursesApi.updateModule(this.courseSlug, module.slug, {
                        title: module.title,
                        description: module.description || '',
                        course: this.courseId,
                        order: newOrder
                    })
                    module.order = newOrder
                } catch (err) {
                    console.error('Failed to update module order:', err)
                    throw err
                }
            }
            
            // Сохраняем порядок уроков для каждого модуля
            for (const module of this.modules) {
                if (!module.lessons || module.lessons.length === 0) {
                    continue
                }
                
                for (let j = 0; j < module.lessons.length; j++) {
                    const lesson = module.lessons[j]
                    const newLessonOrder = j + 1
                    
                    try {
                        await coursesApi.updateLesson(
                            this.courseSlug,
                            module.slug,
                            lesson.slug,
                            {
                                title: lesson.title,
                                module: module.id,
                                order: newLessonOrder,
                                is_published: lesson.is_published
                            }
                        )
                        lesson.order = newLessonOrder
                    } catch (err) {
                        console.error('Failed to update lesson order:', err)
                        throw err
                    }
                }
            }
        },
        
        toggleModule(moduleId) {
            this.expandedModules[moduleId] = !this.expandedModules[moduleId]
            this.expandedModules = { ...this.expandedModules }
        },
        
        onDragStartModule(event, index) {
            this.dragModuleIndex = index
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', index)
        },
        
        onDropModule(event, targetIndex) {
            event.preventDefault()
            
            if (this.dragModuleIndex !== null && this.dragModuleIndex !== targetIndex) {
                const newModules = [...this.modules]
                const [movedItem] = newModules.splice(this.dragModuleIndex, 1)
                newModules.splice(targetIndex, 0, movedItem)
                
                this.modules = newModules.map((item, idx) => ({
                    ...item,
                    order: idx + 1
                }))
                
                this.dragModuleIndex = null
                
                // Сохраняем порядок после перетаскивания
                this.saveAllOrders()
            }
        },
        
        // Drag-and-drop для уроков
        onDragStartLesson(event, moduleId, lessonIndex) {
            this.dragLessonData = { moduleId, lessonIndex }
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', JSON.stringify({ moduleId, lessonIndex }))
        },
        
        onDropLesson(event, targetModuleId, targetLessonIndex) {
            event.preventDefault()
    
            if (!this.dragLessonData) return
            
            const { moduleId: sourceModuleId, lessonIndex: sourceLessonIndex } = this.dragLessonData
            
            if (sourceModuleId === targetModuleId && sourceLessonIndex !== targetLessonIndex) {
                const moduleIndex = this.modules.findIndex(m => m.id === sourceModuleId)
                if (moduleIndex !== -1) {
                    const module = this.modules[moduleIndex]
                    const newLessons = [...module.lessons]
                    const [movedItem] = newLessons.splice(sourceLessonIndex, 1)
                    newLessons.splice(targetLessonIndex, 0, movedItem)
                    
                    module.lessons = newLessons.map((item, idx) => ({
                        ...item,
                        order: idx + 1
                    }))
                    
                    this.modules = [...this.modules]
                    
                    // Сохраняем порядок после перетаскивания
                    this.saveAllOrders()
                }
            }
            
            this.dragLessonData = null
        },
        
        // Module methods
        openModuleModal() {
            this.editingModule = null
            this.moduleForm = { title: '', description: '' }
            this.showModuleModal = true
        },
        
        editModule(module) {
            this.editingModule = module
            this.moduleForm.title = module.title
            this.moduleForm.description = module.description || ''
            this.showModuleModal = true
        },
        
        async saveModule() {
            if (!this.moduleForm.title) {
                this.$toast.warning('Введите название модуля')
                return
            }
            
            try {
                const maxOrder = this.modules.length > 0
                    ? Math.max(...this.modules.map(m => m.order || 0))
                    : 0
                
                const data = {
                    title: this.moduleForm.title,
                    description: this.moduleForm.description,
                    course: this.courseId,
                    order: maxOrder + 1
                }
                
                if (this.editingModule) {
                    await coursesApi.updateModule(this.courseSlug, this.editingModule.slug, data)
                    this.$toast.success('Модуль обновлен')
                } else {
                    await coursesApi.createModule(this.courseSlug, data)
                    this.$toast.success('Модуль создан')
                }
                
                await this.loadCourse()
                this.closeModuleModal()
            } catch (err) {
                console.error('Save module error:', err)
                this.$toast.error('Ошибка при сохранении модуля')
            }
        },
        
        async deleteModule(module) {
            if (confirm(`Удалить модуль "${module.title}"? Все уроки внутри будут удалены.`)) {
                try {
                    await coursesApi.deleteModule(this.courseSlug, module.slug)
                    await this.loadCourse()
                    this.$toast.success('Модуль удален')
                } catch (err) {
                    this.$toast.error('Ошибка при удалении модуля')
                }
            }
        },
        
        closeModuleModal() {
            this.showModuleModal = false
            this.editingModule = null
            this.moduleForm = { title: '', description: '' }
        },
        
        // Lesson methods
        openLessonModal(module) {
            this.currentModuleForLesson = module
            this.editingLesson = null
            this.lessonForm = { title: '', is_published: false }
            this.showLessonModal = true
        },
        
        editLesson(module, lesson) {
            this.currentModuleForLesson = module
            this.editingLesson = lesson
            this.lessonForm.title = lesson.title
            this.lessonForm.is_published = lesson.is_published || false
            this.showLessonModal = true
        },
        
        async saveLesson() {
            if (!this.lessonForm.title) {
                this.$toast.warning('Введите название урока')
                return
            }
            
            try {
                const currentLessons = this.currentModuleForLesson.lessons || []
                const maxOrder = currentLessons.length > 0
                    ? Math.max(...currentLessons.map(l => l.order || 0))
                    : 0
                
                const data = {
                    title: this.lessonForm.title,
                    module: this.currentModuleForLesson.id,
                    order: maxOrder + 1,
                    is_published: this.lessonForm.is_published
                }
                
                if (this.editingLesson) {
                    await coursesApi.updateLesson(
                        this.courseSlug,
                        this.currentModuleForLesson.slug,
                        this.editingLesson.slug,
                        data
                    )
                    this.$toast.success('Урок обновлен')
                } else {
                    await coursesApi.createLesson(
                        this.courseSlug,
                        this.currentModuleForLesson.slug,
                        data
                    )
                    this.$toast.success('Урок создан')
                }
                
                await this.loadCourse()
                this.closeLessonModal()
            } catch (err) {
                console.error('Save lesson error:', err)
                this.$toast.error('Ошибка при сохранении урока')
            }
        },
        
        async deleteLesson(module, lesson) {
            if (confirm(`Удалить урок "${lesson.title}"?`)) {
                try {
                    await coursesApi.deleteLesson(this.courseSlug, module.slug, lesson.slug)
                    await this.loadCourse()
                    this.$toast.success('Урок удален')
                } catch (err) {
                    this.$toast.error('Ошибка при удалении урока')
                }
            }
        },
        
        closeLessonModal() {
            this.showLessonModal = false
            this.editingLesson = null
            this.currentModuleForLesson = null
            this.lessonForm = { title: '', is_published: false }
        },
        
        manageContent(module, lesson) {
            this.$router.push({
                path: `/course/${this.courseSlug}/module/${module.slug}/lesson/${lesson.slug}/content`,
                query: { 
                    moduleTitle: module.title,
                    lessonTitle: lesson.title 
                }
            })
        },
    
        manageTasks(module, lesson) {
            this.$router.push({
                path: `/course/${this.courseSlug}/module/${module.slug}/lesson/${lesson.slug}/tasks`,
                query: { 
                    moduleTitle: module.title,
                    lessonTitle: lesson.title 
                }
            })
        },
        
        goBack() {
            this.$router.push('/my-courses')
        },
        
        async confirmDelete() {
            if (confirm('Вы уверены, что хотите удалить курс? Это действие необратимо.')) {
                try {
                    await coursesApi.deleteCourse(this.courseSlug)
                    this.$toast.success('Курс удален')
                    this.$router.push('/my-courses')
                } catch (err) {
                    this.$toast.error('Ошибка при удалении курса')
                }
            }
        },
    }
}
</script>

<style scoped>
.course-edit {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.course-edit__nav {
    margin-bottom: 0.5rem;
}

.course-edit__header {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 2rem;
}

.course-edit__title {
    font-size: 2rem;
    color: #2c3e50;
    margin: 0;
}

.course-form {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-section {
    border: 1px solid #e9ecef;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 2rem;
    padding: 1rem 1rem;
}

.form-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.form-section__title {
    font-size: 1.25rem;
    margin-bottom: 1.5rem;
    color: #2c3e50;
}

/* Модули */
.modules-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.module-card {
    background: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e9ecef;
}

.module-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #f8f9fa;
}

.drag-handle {
    cursor: grab;
    color: #7f8c8d;
    font-size: 1.2rem;
    user-select: none;
}

.drag-handle:active {
    cursor: grabbing;
}

.module-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

.module-order {
    font-weight: bold;
    color: #2c3e50;
}

.module-title {
    margin: 0;
    font-size: 1.1rem;
    color: #2c3e50;
}

.lesson-count {
    font-size: 0.75rem;
    color: #7f8c8d;
}

.module-actions {
    display: flex;
    gap: 0.5rem;
}

/* Уроки */
.lessons-section {
    padding: 1rem;
    background: white;
}

.lessons-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.lesson-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e9ecef;
}

.drag-handle-small {
    cursor: grab;
    color: #7f8c8d;
    font-size: 1rem;
    user-select: none;
}

.drag-handle-small:active {
    cursor: grabbing;
}

.lesson-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    cursor: pointer;
}

.lesson-order {
    color: #7f8c8d;
    font-size: 0.875rem;
}

.lesson-title {
    color: #2c3e50;
    font-size: 0.875rem;
}

.lesson-badges {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
}

/* Кнопки действий */
.lesson-actions {
    display: flex;
    gap: 0.25rem;
}

/* Кнопка добавления урока */
.add-lesson-btn {
    margin-top: 1rem;
}

/* Пустые состояния */
.empty-modules,
.empty-lessons {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 1rem;
}

/* Инфо хинт */
.info-hint {
    font-size: 0.875rem;
    color: #7f8c8d;
    margin-top: 0.5rem;
    text-align: center;
}

/* Кнопки формы */
.form-base-btn {
    font-size: 0.875rem;
    padding: 0.6rem 0.875rem;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
}

.admin-actions-group {
    display: flex;
    gap: 1rem;
}

/* Адаптивность */
@media (max-width: 768px) {
    .course-edit {
        padding: 1rem;
    }
    
    .course-form {
        padding: 1rem;
    }
    
    .lesson-info {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .lesson-badges {
        margin-left: 0;
    }
    
    .form-actions {
        flex-direction: column-reverse;
        gap: 1rem;
    }
}
</style>