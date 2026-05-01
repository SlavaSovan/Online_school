import apiClient from '../client'

export const coursesApi = {
    // Получение списка курсов с фильтрацией
    getCourses(params = {}) {
        return apiClient.get('/courses/courses', { params }).then(res => res.data)
    },
    
    // Получение курса по slug
    getCourseBySlug(slug) {
        return apiClient.get(`/courses/courses/${slug}`).then(res => res.data)
    },
    
    // Запись на курс
    enrollCourse(slug) {
        return apiClient.post(`/courses/courses/${slug}/enroll`).then(res => res.data)
    },
    
    // Получение моих курсов (записи)
    getMyEnrollments(params = {}) {
        return apiClient.get('/courses/my/enrollments', { params }).then(res => res.data)
    },

    // Получение курсов, где пользователь является владельцем
    getMyOwnerCourses(params = {}) {
        return apiClient.get('/courses/my/courses-owner', { params }).then(res => res.data)
    },
    
    // Получение курсов, где пользователь является ментором
    getMyMentorCourses(params = {}) {
        return apiClient.get('/courses/my/courses', { params }).then(res => res.data)
    },
    
    // Получение контента урока
    getLessonContent(courseSlug, moduleSlug, lessonSlug, params = {}) {
        return apiClient.get(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content`, { params })
            .then(res => res.data)
    },
    
    // Получение конкретного элемента контента
    getContentItem(courseSlug, moduleSlug, lessonSlug, contentId) {
        return apiClient.get(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content/${contentId}`)
            .then(res => res.data)
    },
    
    // Получение содержимого markdown файла
    getMarkdownContent(courseSlug, moduleSlug, lessonSlug, contentId) {
        return apiClient.get(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content/${contentId}/display`)
            .then(res => res.data)
    },
    
    // Получение приватного курса (для редактирования)
    getPrivateCourseBySlug(slug) {
        return apiClient.get(`/courses/private/courses/${slug}`).then(res => res.data)
    },
    
    // Создание курса
    createCourse(data) {
        return apiClient.post('/courses/courses/create', data).then(res => res.data)
    },
    
    // Обновление курса
    updateCourse(slug, data) {
        return apiClient.patch(`/courses/courses/${slug}/edit`, data).then(res => res.data)
    },
    
    // Удаление курса
    deleteCourse(slug) {
        return apiClient.delete(`/courses/courses/${slug}/delete`)
    },
    
    // Получение категорий
    getCategories(params = {}) {
        return apiClient.get('/courses/categories', { params }).then(res => res.data)
    },
    
    // Создание модуля
    createModule(courseSlug, data) {
        return apiClient.post(`/courses/courses/${courseSlug}/modules`, data).then(res => res.data)
    },
    
    // Обновление модуля
    updateModule(courseSlug, moduleSlug, data) {
        return apiClient.patch(`/courses/courses/${courseSlug}/modules/${moduleSlug}`, data).then(res => res.data)
    },
    
    // Удаление модуля
    deleteModule(courseSlug, moduleSlug) {
        return apiClient.delete(`/courses/courses/${courseSlug}/modules/${moduleSlug}`)
    },
    
    // Создание урока
    createLesson(courseSlug, moduleSlug, data) {
        return apiClient.post(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons`, data).then(res => res.data)
    },
    
    // Обновление урока
    updateLesson(courseSlug, moduleSlug, lessonSlug, data) {
        return apiClient.patch(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}`, data).then(res => res.data)
    },
    
    // Удаление урока
    deleteLesson(courseSlug, moduleSlug, lessonSlug) {
        return apiClient.delete(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}`)
    },
    
    // Загрузка контента
    uploadContent(courseSlug, moduleSlug, lessonSlug, formData) {
        return apiClient.post(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(res => res.data)
    },
    
    // Обновление контента
    updateContent(courseSlug, moduleSlug, lessonSlug, contentId, formData) {
        return apiClient.patch(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content/${contentId}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(res => res.data)
    },
    
    // Удаление контента
    deleteContent(courseSlug, moduleSlug, lessonSlug, contentId) {
        return apiClient.delete(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/content/${contentId}`)
    },
    
    // Обновление только порядка модуля
    updateModuleOrder(courseSlug, moduleSlug, order) {
        return apiClient.patch(`/courses/courses/${courseSlug}/modules/${moduleSlug}`, { order })
            .then(res => res.data)
    },

    // Обновление только порядка урока
    updateLessonOrder(courseSlug, moduleSlug, lessonSlug, order) {
        return apiClient.patch(`/courses/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}`, { order })
            .then(res => res.data)
    },
}