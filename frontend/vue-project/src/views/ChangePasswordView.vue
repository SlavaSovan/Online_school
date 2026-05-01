<template>
    <div class="password-container">
      <div class="password-card">
        <h2>Смена пароля</h2>
        <form @submit.prevent="handleChange">
                <base-input
                    v-model="form.old_password"
                    label="Старый пароль"
                    type="password"
                    placeholder="••••••••"
                    required
                    :error="error"
                />

                <base-input
                    v-model="form.new_password"
                    label="Новый пароль"
                    type="password"
                    placeholder="••••••••"
                    required
                />

                <base-input
                    v-model="form.new_password_confirm"
                    label="Подтверждение нового пароля"
                    type="password"
                    placeholder="••••••••"
                    required
                    :error="passwordMismatchError"
                />

                <div v-if="success" class="success-message">{{ success }}</div>

                <base-button
                    type="submit"
                    :disabled="authStore.isLoading"
                >
                    {{ authStore.isLoading ? 'Смена...' : 'Сменить пароль' }}
                </base-button>
            </form>
      </div>
    </div>
</template>
  
<script>
import { reactive, ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
    setup() {
        const authStore = useAuthStore()

        const form = reactive({
            old_password: '',
            new_password: '',
            new_password_confirm: '',
        })

        const error = ref('')
        const success = ref('')

        const passwordMismatchError = computed(() => {
            if (form.new_password && form.new_password_confirm && form.new_password !== form.new_password_confirm) {
                return 'Пароли не совпадают'
            }
            return ''
        })

        const handleChange = async () => {
            error.value = ''
            success.value = ''

            if (form.new_password !== form.new_password_confirm) {
                error.value = 'Новые пароли не совпадают'
                return
            }

            const result = await authStore.changePassword(form)

            if (result.success) {
                success.value = 'Пароль успешно изменен!'
                form.old_password = ''
                form.new_password = ''
                form.new_password_confirm = ''
                setTimeout(() => {
                    success.value = ''
                }, 3000)
            } else {
                error.value = result.error
            }
        }

        return {
            authStore,
            form,
            error,
            success,
            passwordMismatchError,
            handleChange
        }
    }
}
</script>

<style scoped>
.password-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
    padding: 1rem;
}

.password-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

.password-card h2 {
    margin-bottom: 1.5rem;
    text-align: center;
    color: #2c3e50;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.success-message {
    padding: 0.75rem;
    background-color: #e8f8f5;
    border: 1px solid #a3e4d7;
    border-radius: 8px;
    color: #27ae60;
    font-size: 0.875rem;
    text-align: center;
}
</style>