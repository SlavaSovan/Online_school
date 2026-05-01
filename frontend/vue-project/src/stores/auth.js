import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/endpoints/auth'

export const useAuthStore = defineStore('auth', () => {
    // Состояние
    const user = ref(null)
    const isAuthenticated = ref(false)
    const isLoading = ref(false)
    
    // Геттеры
    const fullName = computed(() => {
        if (!user.value) return ''
        return `${user.value.last_name} ${user.value.first_name} ${user.value.patronymic}`.trim()
    })
    
    // Действия
    const initAuth = () => {
        const token = localStorage.getItem('access_token')
        if (token) {
            isAuthenticated.value = true
            fetchProfile()
        }
    }
    
    const fetchProfile = async () => {
      try {
          isLoading.value = true
          const profile = await authApi.getProfile()
          user.value = profile
          isAuthenticated.value = true
      } catch (error) {
          logout()
      } finally {
          isLoading.value = false
      }
    }
    
    const login = async (credentials) => {
        try {
            isLoading.value = true
            const response = await authApi.login(credentials)
            localStorage.setItem('access_token', response.access_token)
            localStorage.setItem('refresh_token', response.refresh_token)
            isAuthenticated.value = true
            await fetchProfile()
            return { success: true }
        } catch (error) {
            return { 
                success: false, 
                error: error.response?.data?.detail || 'Ошибка входа' 
            }
        } finally {
            isLoading.value = false
        }
    }
    
    const register = async (data) => {
        try {
            isLoading.value = true
            await authApi.register(data)
            // После регистрации сразу логиним
            return await login({ email: data.email, password: data.password })
        } catch (error) {
            return { 
                success: false, 
                error: error.response?.data?.detail || 'Ошибка регистрации' 
            }
        } finally {
            isLoading.value = false
        }
    }
    
    const logout = async () => {
        try {
            await authApi.logout()
        } catch (error) {
            console.error('Logout error:', error)
        } finally {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            user.value = null
            isAuthenticated.value = false
        }
    }
    
    const updateProfile = async (data) => {
      try {
          isLoading.value = true
          const updatedUser = await authApi.updateProfile(data)
          user.value = updatedUser
          return { success: true }
      } catch (error) {
          return { 
              success: false, 
              error: error.response?.data?.detail || 'Ошибка обновления профиля' 
          }
      } finally {
          isLoading.value = false
      }
    }
    
    const changePassword = async (data) => {
      try {
          isLoading.value = true
          await authApi.changePassword(data)
          return { success: true }
      } catch (error) {
          return { 
              success: false, 
              error: error.response?.data?.detail || 'Ошибка смены пароля' 
          }
      } finally {
          isLoading.value = false
      }
    }
    
    const deleteProfile = async () => {
      try {
          isLoading.value = true
          await authApi.deleteProfile()
          await logout()
          return { success: true }
      } catch (error) {
          return { 
              success: false, 
              error: error.response?.data?.detail || 'Ошибка удаления аккаунта' 
          }
      } finally {
          isLoading.value = false
      }
    }

    // В computed добавьте
    const isMentor = computed(() => {
        return user.value?.role?.name === 'mentor' || user.value?.role?.name === 'admin'
    })

    const isAdmin = computed(() => {
        return user.value?.role?.name === 'admin'
    })
    
    return {
      user,
      isAuthenticated,
      isLoading,
      fullName,
      initAuth,
      login,
      register,
      logout,
      fetchProfile,
      updateProfile,
      changePassword,
      deleteProfile,
      isMentor,
      isAdmin,
    }
})