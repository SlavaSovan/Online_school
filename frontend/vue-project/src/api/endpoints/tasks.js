import apiClient from '../client'

export const tasksApi = {
    // Получение всех заданий урока
    getLessonTasks(courseSlug, moduleSlug, lessonSlug) {
        return apiClient.get(`/tasks/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/tasks`)
            .then(res => res.data)
    },

    // Получение конкретного задания
    getTask(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}`).then(res => res.data)
    },

    // Создание задания (тест)
    createTestTask(courseSlug, moduleSlug, lessonSlug, data) {
        return apiClient.post(`/tasks/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/tasks/test`, data)
            .then(res => res.data)
    },

    // Создание задания (файл)
    createFileTask(courseSlug, moduleSlug, lessonSlug, data) {
        return apiClient.post(`/tasks/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/tasks/file`, data)
            .then(res => res.data)
    },

    // Создание задания (код)
    createSandboxTask(courseSlug, moduleSlug, lessonSlug, data) {
        return apiClient.post(`/tasks/courses/${courseSlug}/modules/${moduleSlug}/lessons/${lessonSlug}/tasks/sandbox`, data)
            .then(res => res.data)
    },

    // Обновление задания
    updateTask(taskId, data) {
        return apiClient.patch(`/tasks/tasks/${taskId}`, data).then(res => res.data)
    },

    // Удаление задания
    deleteTask(taskId) {
        return apiClient.delete(`/tasks/tasks/${taskId}`).then(res => res.data)
    },

    // Получение вопросов задания
    getTaskQuestions(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}/questions`).then(res => res.data)
    },

    // Создание вопроса
    createQuestion(taskId, data) {
        return apiClient.post(`/tasks/tasks/${taskId}/questions`, data).then(res => res.data)
    },

    // Удаление вопроса
    deleteQuestion(taskId, questionId) {
        return apiClient.delete(`/tasks/tasks/${taskId}/questions/${questionId}`).then(res => res.data)
    },
    
    // Получение состояния задания
    getTaskState(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}/state`).then(res => res.data)
    },

    // Получение всех попыток задания
    getTaskSubmissions(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}/submissions`).then(res => res.data)
    },

    // Получение вопросов для теста
    getTestQuestions(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}/test`).then(res => res.data)
    },

    // Отправка ответов на тест
    submitTest(taskId, answers) {
        return apiClient.post(`/tasks/tasks/${taskId}/submit/test`, { answers }).then(res => res.data)
    },

    // Отправка кода для задания sandbox
    submitSandbox(taskId, code) {
        return apiClient.post(`/tasks/tasks/${taskId}/submit/sandbox`, { code }).then(res => res.data)
    },

    // Запуск кода в песочнице
    runSandbox(taskId, code) {
        return apiClient.post(`/tasks/tasks/${taskId}/sandbox/run`, { code }).then(res => res.data)
    },

    // Отправка файла для задания file
    submitFile(taskId, formData) {
        return apiClient.post(`/tasks/tasks/${taskId}/submit/file`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(res => res.data)
    },

    // Скачивание файла ответа
    downloadSubmission(taskId, submissionId) {
        return apiClient.get(`/tasks/tasks/${taskId}/submissions/${submissionId}/download`, {
            responseType: 'blob'
        })
    },

    // Удаление ответа (только для статуса needs_review)
    deleteSubmission(taskId, submissionId) {
        return apiClient.delete(`/tasks/tasks/${taskId}/submissions/${submissionId}`).then(res => res.data)
    },
    
    // Получение всех ответов на задание (для ментора)
    getSubmissionsForMentor(taskId) {
        return apiClient.get(`/tasks/tasks/${taskId}/submissions/mentor`).then(res => res.data)
    },
    
    // Получение информации о ревью
    getReview(taskId, submissionId) {
        return apiClient.get(`/tasks/tasks/${taskId}/submissions/${submissionId}/review`).then(res => res.data)
    },
    
    // Создание ревью
    createReview(taskId, submissionId, data) {
        return apiClient.post(`/tasks/tasks/${taskId}/submissions/${submissionId}/review`, data).then(res => res.data)
    },
    
    // Обновление ревью
    updateReview(taskId, submissionId, data) {
        return apiClient.patch(`/tasks/tasks/${taskId}/submissions/${submissionId}/review`, data).then(res => res.data)
    },
    
    // Удаление ревью
    deleteReview(taskId, submissionId) {
        return apiClient.delete(`/tasks/tasks/${taskId}/submissions/${submissionId}/review`).then(res => res.data)
    },
}