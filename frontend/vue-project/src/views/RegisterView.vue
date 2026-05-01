<template>
    <div class="register-container">
        <div class="register-card">
            <h2>Регистрация</h2>
            <form @submit.prevent="handleRegister">
                <div class="form-row">
                    <base-input
                        v-model="form.last_name"
                        label="Фамилия"
                        placeholder="Иванов"
                        :error="errors.last_name"
                    />
                    <base-input
                        v-model="form.first_name"
                        label="Имя"
                        placeholder="Иван"
                        :error="errors.first_name"
                    />
                    <base-input
                        v-model="form.patronymic"
                        label="Отчество"
                        placeholder="Иванович"
                    />
                </div>

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

                <base-input
                    v-model="form.password_confirm"
                    label="Подтверждение пароля"
                    type="password"
                    placeholder="••••••••"
                    required
                    :error="errors.password_confirm"
                />

                <div v-if="error" class="error-message">{{ error }}</div>

                <base-button
                    type="submit"
                    :disabled="authStore.isLoading"
                >
                    {{ authStore.isLoading ? 'Регистрация...' : 'Зарегистрироваться' }}
                </base-button>
            </form>
            <p class="login-link">
                Уже есть аккаунт? <router-link to="/login">Войти</router-link>
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
            first_name: '',
            last_name: '',
            patronymic: '',
            password: '',
            password_confirm: '',
        })

        const errors = reactive({
            email: '',
            first_name: '',
            last_name: '',
            password: '',
            password_confirm: ''
        })

        const error = ref('')

        const validateForm = () => {
            let isValid = true
            errors.email = ''
            errors.first_name = ''
            errors.last_name = ''
            errors.password = ''
            errors.password_confirm = ''
            
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
            } else if (form.password.length < 6) {
                errors.password = 'Пароль должен быть не менее 6 символов'
                isValid = false
            }
            
            if (form.password !== form.password_confirm) {
                errors.password_confirm = 'Пароли не совпадают'
                isValid = false
            }
            
            return isValid
        }

        const handleRegister = async () => {
            if (!validateForm()) return
            
            error.value = ''
            const result = await authStore.register(form)
            
            if (result.success) {
                router.push('/')
            } else {
                error.value = result.error
            }
        }

        return {
            authStore,
            form,
            errors,
            error,
            handleRegister
        }
    }
}
</script>
  
<style scoped>
.register-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
    padding: 1rem;
}

.register-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 700px;
}

.register-card h2 {
    margin-bottom: 1.5rem;
    text-align: center;
    color: #2c3e50;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin-bottom: 0.5rem;
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

.login-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.875rem;
    color: #7f8c8d;
}

.login-link a {
    color: #3498db;
    font-weight: 500;
}

.login-link a:hover {
    text-decoration: underline;
}

@media (max-width: 640px) {
    .form-row {
        grid-template-columns: 1fr;
        gap: 0;
    }
}
</style>