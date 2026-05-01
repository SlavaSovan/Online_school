<template>
    <div class="profile-container">
        <div class="profile-card">
            <h2>Профиль пользователя</h2>
            
            <div v-if="authStore.isLoading" class="loading">Загрузка...</div>
            
            <form v-else @submit.prevent="handleUpdate">
                <div class="form-row">
                    <base-input
                        v-model="form.last_name"
                        label="Фамилия"
                        placeholder="Иванов"
                    />
                    <base-input
                        v-model="form.first_name"
                        label="Имя"
                        placeholder="Иван"
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
                    :error="updateError"
                />

                <div v-if="updateSuccess" class="success-message">
                    Профиль успешно обновлен!
                </div>

                <base-button
                    class="save-btn"
                    type="submit"
                    :disabled="isUpdating"
                >
                    {{ isUpdating ? 'Сохранение...' : 'Сохранить изменения' }}
                </base-button>
            </form>

            <div class="actions-section">
                <h3>Действия с аккаунтом</h3>
                <div class="actions-buttons">
                    <base-button @click="goToChangePassword" variant="primary">
                        Сменить пароль
                    </base-button>
                    <base-button @click="handleLogout" variant="secondary">
                        Выйти
                    </base-button>
                    <base-button @click="handleDelete" variant="danger">
                        Удалить аккаунт
                    </base-button>
                </div>
            </div>
        </div>
    </div>
</template>
  
<script>
import { ref, reactive, onMounted } from 'vue'
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
        })

        const isUpdating = ref(false)
        const updateError = ref('')
        const updateSuccess = ref(false)

        onMounted(() => {
            if (authStore.user) {
                form.email = authStore.user.email
                form.first_name = authStore.user.first_name || ''
                form.last_name = authStore.user.last_name || ''
                form.patronymic = authStore.user.patronymic || ''
            }
        })

        const handleUpdate = async () => {
            isUpdating.value = true
            updateError.value = ''
            updateSuccess.value = false
            
            const result = await authStore.updateProfile(form)
            
            if (result.success) {
                updateSuccess.value = true
                setTimeout(() => {
                    updateSuccess.value = false
                }, 3000)
            } else {
                updateError.value = result.error
            }
            
            isUpdating.value = false
        }

        const goToChangePassword = () => {
            router.push('/change-password')
        }

        const handleLogout = async () => {
            await authStore.logout()
            router.push('/login')
        }

        const handleDelete = async () => {
            if (confirm('Вы уверены, что хотите удалить аккаунт? Это действие необратимо.')) {
                await authStore.deleteProfile()
            }
        }

        return {
            authStore,
            form,
            isUpdating,
            updateError,
            updateSuccess,
            handleUpdate,
            goToChangePassword,
            handleLogout,
            handleDelete
        }
    }
}
</script>
  
<style scoped>
.profile-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
    padding: 1rem;
}

.profile-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 700px;
}

.profile-card h2 {
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

.success-message {
    margin-top: 1rem;
    padding: 0.75rem;
    background-color: #e8f8f5;
    border: 1px solid #a3e4d7;
    border-radius: 8px;
    color: #27ae60;
    font-size: 0.875rem;
    text-align: center;
}

.actions-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #eee;
}

.actions-section h3 {
    margin-bottom: 1rem;
    font-size: 1rem;
    color: #7f8c8d;
}

.actions-buttons {
    display: flex;
    gap: 1rem;
}

.loading {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}

.save-btn {
    margin-top: 20px;
}

@media (max-width: 640px) {
    .form-row {
        grid-template-columns: 1fr;
        gap: 0;
    }
    
    .actions-buttons {
        flex-direction: column;
    }
}
</style>