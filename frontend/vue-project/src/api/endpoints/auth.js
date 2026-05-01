import apiClient from '../client'

// API методы

export const authApi = {
    register(data) {
        return apiClient.post('/users/auth/register', data).then(res => res.data)
    },
  
    login(data) {
        return apiClient.post('/users/auth/login', data).then(res => res.data)
    },
    
    logout() {
        return apiClient.post('/users/auth/logout').then(res => res.data)
    },
    
    getProfile() {
        return apiClient.get('/users/auth/profile').then(res => res.data)
    },
    
    updateProfile(data) {
        return apiClient.patch('/users/auth/profile', data).then(res => res.data)
    },
    
    deleteProfile() {
        return apiClient.delete('/users/auth/profile').then(() => undefined)
    },
    
    changePassword(data) {
        return apiClient.post('/users/auth/change-password', data).then(res => res.data)
    },
    
    refreshToken(refreshToken) {
        return apiClient.post('/users/auth/refresh', { refresh_token: refreshToken }).then(res => res.data)
    },

    getUser(userId) {
        return apiClient.get(`/users/users/${userId}`).then(res => res.data)
    },
}