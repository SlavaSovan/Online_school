<template>
    <div class="admin-panel">
        <div class="admin-header">
            <h1>Административная панель</h1>
            <go-back-btn @click="goBack" />
        </div>
        
        <div class="admin-tabs">
            <button 
                v-for="tab in tabs" 
                :key="tab.key"
                class="tab-btn"
                :class="{ active: activeTab === tab.key }"
                @click="activeTab = tab.key"
            >
                {{ tab.label }}
            </button>
        </div>
        
        <div class="admin-content">
            <UsersTable v-if="activeTab === 'users'" />
            <RolesTable v-if="activeTab === 'roles'" />
            <PermissionsTable v-if="activeTab === 'permissions'" />
        </div>
    </div>
</template>

<script>
import UsersTable from '@/components/admin/UsersTable.vue'
import RolesTable from '@/components/admin/RolesTable.vue'
import PermissionsTable from '@/components/admin/PermissionsTable.vue'

export default {
    name: 'AdminView',
    components: { UsersTable, RolesTable, PermissionsTable },
    data() {
        return {
            activeTab: 'users',
            tabs: [
                { key: 'users', label: 'Пользователи' },
                { key: 'roles', label: 'Роли' },
                { key: 'permissions', label: 'Разрешения' }
            ]
        }
    },
    methods: {
        goBack() {
            this.$router.push('/')
        }
    }
}
</script>

<style scoped>
.admin-panel {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #3498db;
}

.admin-header h1 {
    margin: 0;
    font-size: 1.75rem;
    color: #2c3e50;
}

.admin-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid #e9ecef;
}

.tab-btn {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: #7f8c8d;
    transition: all 0.2s;
}

.tab-btn:hover {
    color: #3498db;
}

.tab-btn.active {
    color: #3498db;
    border-bottom: 2px solid #3498db;
    margin-bottom: -1px;
}
</style>