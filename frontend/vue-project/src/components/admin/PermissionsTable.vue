<template>
    <div class="admin-table">
        <div class="table-header">
            <h2>Разрешения</h2>
            <base-button variant="primary" @click="openCreateModal">+ Создать разрешение</base-button>
        </div>
        
        <div class="table-filters">
            <base-input
                v-model="search"
                placeholder="Поиск по названию или описанию..."
                class="filter-search"
                @input="filterPermissions"
            />
        </div>
        
        <div v-if="loading" class="table-loading">
            Загрузка...
        </div>
        
        <div v-else-if="error" class="table-error">
            {{ error }}
            <base-button @click="loadPermissions">Повторить</base-button>
        </div>
        
        <div v-else class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Название</th>
                        <th>Описание</th>
                        <th>Категория</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="perm in filteredPermissions" :key="perm.id">
                        <td>{{ perm.id }}</td>
                        <td><code>{{ perm.name }}</code></td>
                        <td>{{ perm.description || '-' }}</td>
                        <td>{{ perm.category || '-' }}</td>
                        <td class="actions">
                            <action-icon variant="edit" @click="openEditModal(perm)" title="Редактировать" />
                            <action-icon variant="delete" @click="confirmDelete(perm)" title="Удалить" />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Модальное окно создания/редактирования -->
        <Modal
            :visible="showModal"
            :title="editingPermission ? 'Редактирование разрешения' : 'Создание разрешения'"
            confirm-text="Сохранить"
            @close="closeModal"
            @confirm="savePermission"
        >
            <div class="modal-form">
                <base-input
                    v-model="form.name"
                    label="Название разрешения"
                    placeholder="users.view, courses.edit"
                    required
                />
                <base-input
                    v-model="form.description"
                    label="Описание"
                    type="textarea"
                    placeholder="Описание разрешения"
                />
                <base-input
                    v-model="form.category"
                    label="Категория"
                    placeholder="users, courses, tasks"
                />
            </div>
        </Modal>
    </div>
</template>

<script>
import { adminApi } from '@/api/endpoints/admin'
import Modal from '@/components/Modal.vue'

export default {
    name: 'PermissionsTable',
    components: { Modal },
    data() {
        return {
            permissions: [],
            filteredPermissions: [],
            loading: false,
            error: null,
            search: '',
            showModal: false,
            editingPermission: null,
            form: {
                name: '',
                description: '',
                category: ''
            }
        }
    },
    async mounted() {
        await this.loadPermissions()
    },
    methods: {
        async loadPermissions() {
            this.loading = true
            this.error = null
            
            try {
                this.permissions = await adminApi.getPermissions()
                this.filteredPermissions = [...this.permissions]
            } catch (err) {
                console.error('Failed to load permissions:', err)
                this.error = 'Не удалось загрузить разрешения'
            } finally {
                this.loading = false
            }
        },
        
        filterPermissions() {
            if (!this.search) {
                this.filteredPermissions = [...this.permissions]
            } else {
                const searchLower = this.search.toLowerCase()
                this.filteredPermissions = this.permissions.filter(perm =>
                    perm.name.toLowerCase().includes(searchLower) ||
                    (perm.description && perm.description.toLowerCase().includes(searchLower)) ||
                    (perm.category && perm.category.toLowerCase().includes(searchLower))
                )
            }
        },
        
        openCreateModal() {
            this.editingPermission = null
            this.form = {
                name: '',
                description: '',
                category: ''
            }
            this.showModal = true
        },
        
        openEditModal(perm) {
            this.editingPermission = perm
            this.form = {
                name: perm.name,
                description: perm.description || '',
                category: perm.category || ''
            }
            this.showModal = true
        },
        
        closeModal() {
            this.showModal = false
            this.editingPermission = null
        },
        
        async savePermission() {
            if (!this.form.name) {
                this.$toast.warning('Введите название разрешения')
                return
            }
            
            try {
                if (this.editingPermission) {
                    await adminApi.updatePermission(this.editingPermission.id, {
                        description: this.form.description,
                        category: this.form.category
                    })
                    this.$toast.success('Разрешение обновлено')
                } else {
                    await adminApi.createPermission({
                        name: this.form.name,
                        description: this.form.description,
                        category: this.form.category
                    })
                    this.$toast.success('Разрешение создано')
                }
                this.closeModal()
                await this.loadPermissions()
            } catch (err) {
                console.error('Failed to save permission:', err)
                this.$toast.error('Ошибка при сохранении')
            }
        },
        
        async confirmDelete(perm) {
            if (confirm(`Удалить разрешение "${perm.name}"?`)) {
                try {
                    await adminApi.deletePermission(perm.id)
                    this.$toast.success('Разрешение удалено')
                    await this.loadPermissions()
                } catch (err) {
                    console.error('Failed to delete permission:', err)
                    this.$toast.error('Ошибка при удалении')
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
    margin-bottom: 1.5rem;
}

.filter-search {
    max-width: 300px;
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

.data-table code {
    background: #f8f9fa;
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.875rem;
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
</style>