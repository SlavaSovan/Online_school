import apiClient from '../client'

export const adminApi = {
    // ============ Пользователи ============
    getUsers(params = {}) {
        return apiClient.get('/users/users', { params }).then(res => res.data)
    },
    
    getUser(userId) {
        return apiClient.get(`/users/users/${userId}`).then(res => res.data)
    },
    
    createUser(data) {
        return apiClient.post('/users/users', data).then(res => res.data)
    },
    
    updateUser(userId, data) {
        return apiClient.patch(`/users/users/${userId}`, data).then(res => res.data)
    },
    
    deleteUser(userId) {
        return apiClient.delete(`/users/users/${userId}`)
    },
    
    activateUser(userId) {
        return apiClient.patch(`/users/users/${userId}/activate`).then(res => res.data)
    },
    
    deactivateUser(userId) {
        return apiClient.patch(`/users/users/${userId}/deactivate`).then(res => res.data)
    },
    
    updateUserRole(userId, roleId) {
        return apiClient.patch(`/users/users/${userId}/role`, { role_id: roleId }).then(res => res.data)
    },
    
    getUsersByRole(roleId, params = {}) {
        return apiClient.get(`/users/users/roles/${roleId}`, { params }).then(res => res.data)
    },
    
    // ============ Роли ============
    getRoles() {
        return apiClient.get('/users/roles').then(res => res.data)
    },
    
    getRole(roleId) {
        return apiClient.get(`/users/roles/${roleId}`).then(res => res.data)
    },
    
    createRole(data) {
        return apiClient.post('/users/roles', data).then(res => res.data)
    },
    
    updateRole(roleId, data) {
        return apiClient.patch(`/users/roles/${roleId}`, data).then(res => res.data)
    },
    
    deleteRole(roleId) {
        return apiClient.delete(`/users/roles/${roleId}`)
    },
    
    setDefaultRole(roleId) {
        return apiClient.patch(`/users/roles/${roleId}/set-default`).then(res => res.data)
    },
    
    setRolePermissions(roleId, permissionIds) {
        return apiClient.put(`/users/roles/${roleId}/permissions`, permissionIds).then(res => res.data)
    },
    
    addRolePermission(roleId, permissionId) {
        return apiClient.post(`/users/roles/${roleId}/permissions/${permissionId}`).then(res => res.data)
    },
    
    removeRolePermission(roleId, permissionId) {
        return apiClient.delete(`/users/roles/${roleId}/permissions/${permissionId}`).then(res => res.data)
    },
    
    // ============ Разрешения ============
    getPermissions() {
        return apiClient.get('/users/permissions').then(res => res.data)
    },
    
    getPermission(permissionId) {
        return apiClient.get(`/users/permissions/${permissionId}`).then(res => res.data)
    },
    
    createPermission(data) {
        return apiClient.post('/users/permissions', data).then(res => res.data)
    },
    
    updatePermission(permissionId, data) {
        return apiClient.patch(`/users/permissions/${permissionId}`, data).then(res => res.data)
    },
    
    deletePermission(permissionId) {
        return apiClient.delete(`/users/permissions/${permissionId}`)
    }
}