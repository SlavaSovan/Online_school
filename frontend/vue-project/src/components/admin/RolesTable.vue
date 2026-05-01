<template>
    <div class="admin-table">
        <div class="table-header">
            <h2>Роли</h2>
            <base-button variant="primary" @click="openCreateModal">+ Создать роль</base-button>
        </div>
        
        <div v-if="loading" class="table-loading">
            Загрузка...
        </div>
        
        <div v-else-if="error" class="table-error">
            {{ error }}
            <base-button @click="loadRoles">Повторить</base-button>
        </div>
        
        <div v-else class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Название</th>
                        <th>Описание</th>
                        <th>По умолчанию</th>
                        <th>Кол-во пользователей</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="role in roles" :key="role.id">
                        <td>{{ role.id }}</td>
                        <td>{{ role.name }}</td>
                        <td>{{ role.description || '-' }}</td>
                        <td>
                            <badge :variant="role.is_default ? 'success' : 'info'" :label="role.is_default ? 'Да' : 'Нет'" />
                        </td>
                        <td>{{ role.user_count || 0 }}</td>
                        <td class="actions">
                            <action-icon variant="edit" @click="openEditModal(role)" title="Редактировать" />
                            <action-icon variant="permissions" @click="managePermissions(role)" title="Управление разрешениями" />
                            <action-icon variant="delete" @click="confirmDelete(role)" title="Удалить" />
                            <action-icon 
                                v-if="!role.is_default" 
                                variant="star" 
                                @click="confirmSetDefault(role)" 
                                title="Сделать ролью по умолчанию" 
                            />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Модальное окно создания/редактирования -->
        <Modal
            :visible="showModal"
            :title="editingRole ? 'Редактирование роли' : 'Создание роли'"
            confirm-text="Сохранить"
            @close="closeModal"
            @confirm="saveRole"
        >
            <div class="modal-form">
                <base-input
                    v-model="form.name"
                    label="Название роли"
                    placeholder="admin, mentor, student"
                    required
                />
                <base-input
                    v-model="form.description"
                    label="Описание"
                    type="textarea"
                    placeholder="Описание роли"
                />
                <base-checkbox
                    v-if="!editingRole"
                    v-model="form.is_default"
                    label="Сделать ролью по умолчанию"
                />
            </div>
        </Modal>
        
        <!-- Модальное окно управления разрешениями -->
        <Modal
            :visible="showPermissionsModal"
            :title="`Управление разрешениями: ${currentRole?.name}`"
            class="permissions-modal"
            confirm-text="Закрыть"
            width="large"
            @close="closePermissionsModal"
            @confirm="closePermissionsModal"
        >
            <div class="permissions-editor">
                <!-- Форма добавления нового разрешения -->
                <div class="add-permission-form">
                    <base-select
                        v-model="selectedPermissionToAdd"
                        :options="availablePermissionsOptions"
                        placeholder="Выберите разрешение для добавления"
                        class="permission-select"
                    />
                    <base-button 
                        variant="primary" 
                        @click="addPermission"
                        :disabled="!selectedPermissionToAdd"
                    >
                        + Добавить
                    </base-button>
                </div>
                
                <!-- Список разрешений по категориям -->
                <div class="permissions-list">
                    <div v-if="currentRolePermissions.length === 0" class="empty-permissions">
                        <p>Нет назначенных разрешений</p>
                    </div>
                    <div v-else class="permissions-category" v-for="(perms, category) in groupedCurrentPermissions" :key="category">
                        <h4 class="category-title">{{ category || 'Без категории' }}</h4>
                        <div class="permissions-grid">
                            <div v-for="perm in perms" :key="perm.id" class="permission-item">
                                <div class="permission-info">
                                    <span class="permission-name">{{ perm.name }}</span>
                                    <span class="permission-desc" :title="perm.description">{{ perm.description }}</span>
                                </div>
                                <action-icon variant="delete" @click="removePermission(perm.id)" title="Удалить разрешение" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Modal>
    </div>
</template>

<script>
import { adminApi } from '@/api/endpoints/admin'
import Modal from '@/components/Modal.vue'

export default {
    name: 'RolesTable',
    components: { Modal },
    data() {
        return {
            roles: [],
            permissions: [],
            loading: false,
            error: null,
            showModal: false,
            editingRole: null,
            form: {
                name: '',
                description: '',
                is_default: false
            },
            showPermissionsModal: false,
            currentRole: null,
            currentRolePermissions: [],
            selectedPermissionToAdd: null
        }
    },
    computed: {
        groupedPermissions() {
            const grouped = {}
            for (const perm of this.permissions) {
                const category = perm.category || 'Другие'
                if (!grouped[category]) {
                    grouped[category] = []
                }
                grouped[category].push(perm)
            }
            return grouped
        },
        
        groupedCurrentPermissions() {
            const grouped = {}
            for (const perm of this.currentRolePermissions) {
                const category = perm.category || 'Без категории'
                if (!grouped[category]) {
                    grouped[category] = []
                }
                grouped[category].push(perm)
            }
            // Сортируем по имени в каждой категории
            for (const category in grouped) {
                grouped[category].sort((a, b) => a.name.localeCompare(b.name))
            }
            return grouped
        },
        
        availablePermissionsOptions() {
            const assignedIds = new Set(this.currentRolePermissions.map(p => p.id))
            return this.permissions
                .filter(p => !assignedIds.has(p.id))
                .map(p => ({
                    value: p.id,
                    label: `${p.name}${p.category ? ` (${p.category})` : ''}${p.description ? ` - ${p.description}` : ''}`
                }))
        },
    },
    async mounted() {
        await this.loadRoles()
        await this.loadPermissions()
    },
    methods: {
        async loadRoles() {
            this.loading = true
            this.error = null
            
            try {
                this.roles = await adminApi.getRoles()
            } catch (err) {
                console.error('Failed to load roles:', err)
                this.error = 'Не удалось загрузить роли'
            } finally {
                this.loading = false
            }
        },
        
        async loadPermissions() {
            try {
                this.permissions = await adminApi.getPermissions()
            } catch (err) {
                console.error('Failed to load permissions:', err)
            }
        },
        
        openCreateModal() {
            this.editingRole = null
            this.form = {
                name: '',
                description: '',
                is_default: false
            }
            this.showModal = true
        },
        
        openEditModal(role) {
            this.editingRole = role
            this.form = {
                name: role.name,
                description: role.description || '',
                is_default: role.is_default
            }
            this.showModal = true
        },
        
        closeModal() {
            this.showModal = false
            this.editingRole = null
        },
        
        async saveRole() {
            if (!this.form.name) {
                this.$toast.warning('Введите название роли')
                return
            }
            
            try {
                if (this.editingRole) {
                    await adminApi.updateRole(this.editingRole.id, {
                        name: this.form.name,
                        description: this.form.description
                    })
                    this.$toast.success('Роль обновлена')
                } else {
                    await adminApi.createRole({
                        name: this.form.name,
                        description: this.form.description,
                        is_default: this.form.is_default
                    })
                    this.$toast.success('Роль создана')
                }
                this.closeModal()
                await this.loadRoles()
            } catch (err) {
                console.error('Failed to save role:', err)
                this.$toast.error('Ошибка при сохранении')
            }
        },
        
        async confirmDelete(role) {
            if (role.is_default) {
                this.$toast.warning('Нельзя удалить роль по умолчанию')
                return
            }
            
            if (confirm(`Удалить роль "${role.name}"?`)) {
                try {
                    await adminApi.deleteRole(role.id)
                    this.$toast.success('Роль удалена')
                    await this.loadRoles()
                } catch (err) {
                    console.error('Failed to delete role:', err)
                    this.$toast.error('Ошибка при удалении')
                }
            }
        },
        
        async confirmSetDefault(role) {
            if (confirm(`Сделать "${role.name}" ролью по умолчанию?`)) {
                try {
                    await adminApi.setDefaultRole(role.id)
                    this.$toast.success('Роль по умолчанию обновлена')
                    await this.loadRoles()
                } catch (err) {
                    console.error('Failed to set default role:', err)
                    this.$toast.error('Ошибка при установке')
                }
            }
        },
        
        async managePermissions(role) {
            this.currentRole = role
            this.selectedPermissionToAdd = null
            
            try {
                const roleData = await adminApi.getRole(role.id)
                this.currentRolePermissions = roleData.permissions || []
                this.showPermissionsModal = true
            } catch (err) {
                console.error('Failed to load role permissions:', err)
                this.$toast.error('Ошибка загрузки разрешений')
            }
        },
        
        async addPermission() {
            if (!this.selectedPermissionToAdd) return
            
            try {
                await adminApi.addRolePermission(this.currentRole.id, this.selectedPermissionToAdd)
                // Обновляем список разрешений
                const roleData = await adminApi.getRole(this.currentRole.id)
                this.currentRolePermissions = roleData.permissions || []
                this.selectedPermissionToAdd = null
                this.$toast.success('Разрешение добавлено')
            } catch (err) {
                console.error('Failed to add permission:', err)
                this.$toast.error('Ошибка при добавлении разрешения')
            }
        },
        
        async removePermission(permId) {
            try {
                await adminApi.removeRolePermission(this.currentRole.id, permId)
                this.currentRolePermissions = this.currentRolePermissions.filter(p => p.id !== permId)
                this.$toast.success('Разрешение удалено')
            } catch (err) {
                console.error('Failed to remove permission:', err)
                this.$toast.error('Ошибка при удалении разрешения')
            }
        },
        
        closePermissionsModal() {
            this.showPermissionsModal = false
            this.currentRole = null
            this.currentRolePermissions = []
            this.selectedPermissionToAdd = null
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

.modal-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

/* Стили для редактора разрешений */

:deep(.permissions-modal .modal) {
    max-width: 900px !important;
    min-width: 600px !important;
    width: 95% !important;
}

.permissions-editor {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-height: 70vh;
    overflow-y: auto;
}

.add-permission-form {
    display: flex;
    gap: 1rem;
    align-items: flex-end;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.permission-select {
    flex: 1;
}

.permissions-list {
    min-height: 200px;
}

.empty-permissions {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
    background: #f8f9fa;
    border-radius: 8px;
}

.permissions-category {
    margin-bottom: 1.5rem;
}

.category-title {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3498db;
    color: #2c3e50;
}

.permissions-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.permission-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.permission-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.permission-name {
    font-weight: 500;
    font-family: monospace;
    font-size: 0.875rem;
    color: #2c3e50;
}

.permission-desc {
    font-size: 0.7rem;
    color: #7f8c8d;
}
</style>