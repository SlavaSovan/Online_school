import axios from 'axios'

// URL бэкенда (можно вынести в .env)
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost/api'

// Создаем axios инстанс
const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
})

// Флаг для предотвращения множественных рефрешей
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token) => {
    failedQueue.forEach((promise) => {
        if (error) {
            promise.reject(error)
        } else {
            promise.resolve(token)
        }
    })
    failedQueue = []
}

// Интерцептор для добавления access_token
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Интерцептор для обработки ошибок и рефреша
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        originalRequest._retry = originalRequest._retry || false
        
        // Если ошибка 401/403 и это не повторный запрос
        if ((error.response?.status === 401 || error.response?.status === 403) && !originalRequest._retry) {
          
            // Если уже идет рефреш — добавляем в очередь
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                  failedQueue.push({ resolve, reject })
                })
                    .then((token) => {
                      originalRequest.headers.Authorization = `Bearer ${token}`
                      return apiClient(originalRequest)
                    })
                    .catch((err) => Promise.reject(err))
            }

            originalRequest._retry = true
            isRefreshing = true

            const refreshToken = localStorage.getItem('refresh_token')
            
            if (!refreshToken) {
                // Нет рефреш токена — выходим
                processQueue(new Error('No refresh token'), null)
                isRefreshing = false
                // Очищаем данные и редиректим на логин
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                window.location.href = '/login'
                return Promise.reject(error)
            }

            try {
                // Пытаемся обновить токены
                const response = await axios.post(`${BASE_URL}/users/auth/refresh`, {
                  refresh_token: refreshToken,
                })
                
                const { access_token, refresh_token } = response.data
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('refresh_token', refresh_token)
                
                // Обрабатываем очередь запросов
                processQueue(null, access_token)
                isRefreshing = false
                
                // Повторяем оригинальный запрос
                originalRequest.headers.Authorization = `Bearer ${access_token}`
                return apiClient(originalRequest)
            } catch (refreshError) {
              // Рефреш не удался — очищаем всё и идем на логин
                processQueue(refreshError, null)
                isRefreshing = false
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                window.location.href = '/login'
                return Promise.reject(refreshError)
            }
        }
        
        return Promise.reject(error)
    }
)

export default apiClient