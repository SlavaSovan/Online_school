import apiClient from '../client'

let categoriesCache = null
let cacheTime = null
const CACHE_DURATION = 30 * 60 * 1000 // 30 минут

export const categoriesApi = {
    async getCategories(params = {}) {
        // Проверяем кэш
        if (categoriesCache && cacheTime && (Date.now() - cacheTime) < CACHE_DURATION) {
            return categoriesCache
        }
        
        const response = await apiClient.get('/courses/categories', { params })
        categoriesCache = response.data
        cacheTime = Date.now()
        return response.data
    },
    
    clearCache() {
        categoriesCache = null
        cacheTime = null
    }
}