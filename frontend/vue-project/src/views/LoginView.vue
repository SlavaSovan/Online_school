<template>
    <div class="login-container">
        <div class="login-card">
            <h2>Вход в систему</h2>

            <form @submit.prevent="handleLogin">
                <base-input
                    v-model="form.email"
                    label="Email"
                    type="email"
                    placeholder="user@example.com"
                    required
                    :error="errors.email"
                />

                <base-input
                    v-model="form.password"
                    label="Пароль"
                    type="password"
                    placeholder="••••••••"
                    required
                    :error="errors.password"
                />

                <div v-if="loginError" class="error-message">
                    {{ loginError }}
                </div>
        
                <base-button
                    type="submit"
                    :disabled="authStore.isLoading"
                    @click="handleLogin"
                >
                    {{ authStore.isLoading ? 'Вход...' : 'Войти' }}
                </base-button>
            </form>

            <p class="register-link">
                Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
            </p>
        </div>
    </div>
</template>
  
<script>
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

export default {
    setup() {
        const authStore = useAuthStore()
        const router = useRouter()

        const form = reactive({
            email: '',
            password: '',
        })

        const errors = reactive({
            email: '',
            password: ''
        })

        const loginError = ref('')

        const validateForm = () => {
            let isValid = true
            errors.email = ''
            errors.password = ''
            
            if (!form.email) {
                errors.email = 'Email обязателен'
                isValid = false
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
                errors.email = 'Введите корректный email'
                isValid = false
            }
            
            if (!form.password) {
                errors.password = 'Пароль обязателен'
                isValid = false
            }
            
            return isValid
        }

        const handleLogin = async () => {
            if (!validateForm()) return
            
            loginError.value = ''
            const result = await authStore.login(form)

            if (result.success) {
                router.push('/')
            } else {
                loginError.value = result.error
            }
        }

        return {
            authStore,
            form,
            errors,
            loginError,
            handleLogin
        }
    }
}
</script>
  
<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
    padding: 1rem;
}

.login-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

.login-card h2 {
    margin-bottom: 1.5rem;
    text-align: center;
    color: #2c3e50;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.error-message {
    padding: 0.75rem;
    background-color: #fee;
    border: 1px solid #fcc;
    border-radius: 8px;
    color: #e74c3c;
    font-size: 0.875rem;
    text-align: center;
}

.register-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.875rem;
    color: #7f8c8d;
}

.register-link a {
    color: #3498db;
    font-weight: 500;
}

.register-link a:hover {
    text-decoration: underline;
}
</style>