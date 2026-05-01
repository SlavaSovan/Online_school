<template>
    <div class="admin-table">
        <div class="table-header">
            <h2>Пользователи</h2>
            <base-button variant="primary" @click="openCreateModal">+ Создать пользователя</base-button>
        </div>
        
        <div class="table-filters">
            <base-input
                v-model="filters.search"
                placeholder="Поиск по email или имени..."
                class="filter-search"
                @input="loadUsers"
            />
            <base-checkbox
                v-model="filters.include_inactive"
                label="Включая неактивных"
                @update:modelValue="loadUsers"
            />
            <base-select
                v-model="filters.role_id"
                :options="roleOptions"
                placeholder="Все роли"
                class="filter-role"
                @update:modelValue="loadUsers"
            />
        </div>
        
        <div v-if="loading" class="table-loading">
            Загрузка...
        </div>
        
        <div v-else-if="error" class="table-error">
            {{ error }}
            <base-button @click="loadUsers">Повторить</base-button>
        </div>
        
        <div v-else class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Email</th>
                        <th>Фамилия</th>
                        <th>Имя</th>
                        <th>Отчество</th>
                        <th>Роль</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="user in users" :key="user.id">
                        <td>{{ user.id }}</td>
                        <td>{{ user.email }}</td>
                        <td>{{ user.last_name || '-' }}</td>
                        <td>{{ user.first_name || '-' }}</td>
                        <td>{{ user.patronymic || '-' }}</td>
                        <td>
                            <badge variant="info" :label="user.role?.name || 'Не назначена'" />
                        </td>
                        <td>
                            <badge :variant="user.is_active ? 'success' : 'danger'" :label="user.is_active ? 'Активен' : 'Заблокирован'" />
                        </td>
                        <td class="actions">
                            <action-icon variant="edit" @click="openEditModal(user)" title="Редактировать" />
                            <action-icon variant="delete" @click="confirmDelete(user)" title="Удалить" />
                            <action-icon 
                                v-if="user.is_active" 
                                variant="deactivate" 
                                @click="confirmDeactivate(user)" 
                                title="Заблокировать" 
                            />
                            <action-icon 
                                v-else 
                                variant="activate" 
                                @click="confirmActivate(user)" 
                                title="Активировать" 
                            />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Пагинация -->
        <div class="table-pagination">
            <base-button 
                variant="secondary" 
                :disabled="skip === 0" 
                @click="changePage(-1)"
            >
                Предыдущая
            </base-button>
            <span class="pagination-info">
                {{ skip + 1 }}-{{ skip + users.length }} из {{ total }}
            </span>
            <base-button 
                variant="secondary" 
                :disabled="skip + limit >= total" 
                @click="changePage(1)"
            >
                Следующая
            </base-button>
        </div>
        
        <!-- Модальное окно создания/редактирования -->
        <Modal
            :visible="showModal"
            :title="editingUser ? 'Редактирование пользователя' : 'Создание пользователя'"
            confirm-text="Сохранить"
            @close="closeModal"
            @confirm="saveUser"
        >
            <div class="modal-form">
                <base-input
                    v-model="form.email"
                    label="Email"
                    type="email"
                    required
                />
                <base-input
                    v-model="form.last_name"
                    label="Фамилия"
                />
                <base-input
                    v-model="form.first_name"
                    label="Имя"
                />
                <base-input
                    v-model="form.patronymic"
                    label="Отчество"
                />
                <base-select
                    v-model="form.role_id"
                    label="Роль"
                    :options="roleOptions"
                    required
                />
                <template v-if="!editingUser">
                    <base-input
                        v-model="form.password"
                        label="Пароль"
                        type="password"
                        required
                    />
                    <base-input
                        v-model="form.password_confirm"
                        label="Подтверждение пароля"
                        type="password"
                        required
                    />
                </template>
                <base-checkbox
                    v-if="editingUser"
                    v-model="form.is_active"
                    label="Активен"
                />
            </div>
        </Modal>
    </div>
</template>

<script>
import { adminApi } from '@/api/endpoints/admin'
import Modal from '@/components/Modal.vue'

export default {
    name: 'UsersTable',
    components: { Modal },
    data() {
        return {
            users: [],
            roles: [],
            loading: false,
            error: null,
            skip: 0,
            limit: 20,
            total: 0,
            filters: {
                search: '',
                include_inactive: false,
                role_id: ''
            },
            showModal: false,
            editingUser: null,
            form: {
                email: '',
                last_name: '',
                first_name: '',
                patronymic: '',
                role_id: null,
                is_active: true,
                password: '',
                password_confirm: ''
            }
        }
    },
    computed: {
        roleOptions() {
            return [
                { value: '', label: 'Все роли' },
                ...this.roles.map(r => ({ value: r.id, label: r.name }))
            ]
        }
    },
    async mounted() {
        await this.loadRoles()
        await this.loadUsers()
    },
    methods: {
        
        async loadRoles() {
            try {
                this.roles = await adminApi.getRoles()
            } catch (err) {
                console.error('Failed to load roles:', err)
            }
        },
        
        async loadUsers() {
            this.loading = true
            this.error = null
            
            try {
                const params = {
                    skip: this.skip,
                    limit: this.limit,
                    include_inactive: this.filters.include_inactive
                }
                if (this.filters.search) {
                    params.search = this.filters.search
                }
                if (this.filters.role_id) {
                    const response = await adminApi.getUsersByRole(this.filters.role_id, params)
                    this.users = response.users || []
                    this.total = response.total || 0
                } else {
                    const response = await adminApi.getUsers(params)
                    this.users = response.users || []
                    this.total = response.total || 0
                }
            } catch (err) {
                console.error('Failed to load users:', err)
                this.error = 'Не удалось загрузить пользователей'
            } finally {
                this.loading = false
            }
        },
        
        changePage(delta) {
            const newSkip = this.skip + delta * this.limit
            if (newSkip >= 0 && newSkip < this.total) {
                this.skip = newSkip
                this.loadUsers()
            }
        },
        
        openCreateModal() {
            this.editingUser = null
            this.form = {
                email: '',
                last_name: '',
                first_name: '',
                patronymic: '',
                role_id: null,
                is_active: true,
                password: '',
                password_confirm: ''
            }
            this.showModal = true
        },
        
        openEditModal(user) {
            this.editingUser = user
            this.form = {
                email: user.email,
                last_name: user.last_name || '',
                first_name: user.first_name || '',
                patronymic: user.patronymic || '',
                role_id: user.role_id,
                is_active: user.is_active,
                password: '',
                password_confirm: ''
            }
            this.showModal = true
        },
        
        closeModal() {
            this.showModal = false
            this.editingUser = null
        },
        
        async saveUser() {
            if (!this.form.email) {
                this.$toast.warning('Введите email')
                return
            }
            
            if (!this.editingUser && this.form.password !== this.form.password_confirm) {
                this.$toast.warning('Пароли не совпадают')
                return
            }
            
            try {
                if (this.editingUser) {
                    await adminApi.updateUser(this.editingUser.id, {
                        email: this.form.email,
                        last_name: this.form.last_name,
                        first_name: this.form.first_name,
                        patronymic: this.form.patronymic,
                        is_active: this.form.is_active,
                        role_id: this.form.role_id
                    })
                    if (this.form.role_id !== this.editingUser.role_id) {
                        await adminApi.updateUserRole(this.editingUser.id, this.form.role_id)
                    }
                    this.$toast.success('Пользователь обновлен')
                } else {
                    await adminApi.createUser({
                        email: this.form.email,
                        last_name: this.form.last_name,
                        first_name: this.form.first_name,
                        patronymic: this.form.patronymic,
                        password: this.form.password,
                        password_confirm: this.form.password_confirm,
                        role_id: this.form.role_id
                    })
                    this.$toast.success('Пользователь создан')
                }
                this.closeModal()
                await this.loadUsers()
            } catch (err) {
                console.error('Failed to save user:', err)
                this.$toast.error('Ошибка при сохранении')
            }
        },
        
        async confirmDelete(user) {
            if (confirm(`Удалить пользователя "${user.email}"?`)) {
                try {
                    await adminApi.deleteUser(user.id)
                    this.$toast.success('Пользователь удален')
                    await this.loadUsers()
                } catch (err) {
                    console.error('Failed to delete user:', err)
                    this.$toast.error('Ошибка при удалении')
                }
            }
        },
        
        async confirmActivate(user) {
            if (confirm(`Активировать пользователя "${user.email}"?`)) {
                try {
                    await adminApi.activateUser(user.id)
                    this.$toast.success('Пользователь активирован')
                    await this.loadUsers()
                } catch (err) {
                    console.error('Failed to activate user:', err)
                    this.$toast.error('Ошибка при активации')
                }
            }
        },
        
        async confirmDeactivate(user) {
            if (confirm(`Заблокировать пользователя "${user.email}"?`)) {
                try {
                    await adminApi.deactivateUser(user.id)
                    this.$toast.success('Пользователь заблокирован')
                    await this.loadUsers()
                } catch (err) {
                    console.error('Failed to deactivate user:', err)
                    this.$toast.error('Ошибка при блокировке')
                }
            }
        }
    }
}
</script>

<style scoped>
.admin-table {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    gap: 1rem;
}

.table-header h2 {
    margin: 0;
    font-size: 1.25rem;
    color: #2c3e50;
}

.table-filters {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.filter-search {
    flex: 2;
    min-width: 200px;
}

.filter-role {
    min-width: 150px;
    justify-content: center;
}

.table-wrapper {
    overflow-x: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th,
.data-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e9ecef;
}

.data-table th {
    background: #f8f9fa;
    font-weight: 600;
    color: #2c3e50;
}

.data-table td {
    color: #495057;
}

.actions {
    display: flex;
    gap: 0.5rem;
}

.table-loading,
.table-error {
    text-align: center;
    padding: 2rem;
}

.table-error {
    color: #e74c3c;
}

.table-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e9ecef;
}

.pagination-info {
    font-size: 0.875rem;
    color: #7f8c8d;
}

.modal-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>