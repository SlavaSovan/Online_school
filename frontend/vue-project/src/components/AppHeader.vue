<template>
    <header class="header">
        <nav class="navbar">
        <div class="logo">
            <router-link to="/">Онлайн-школа</router-link>
        </div>
        <div class="nav-links">
            <router-link to="/">Главная</router-link>
            <router-link to="/catalog">Каталог</router-link>
            <router-link v-if="isAuthenticated" to="/my-courses">Мои курсы</router-link>
            <router-link v-if="isAuthenticated" to="/profile">Профиль</router-link>
            <router-link v-if="isAdmin" to="/admin">Админ-панель</router-link>
            
            <router-link v-if="!isAuthenticated" to="/login">Вход</router-link>
            <router-link v-if="!isAuthenticated" to="/register">Регистрация</router-link>
        </div>
        </nav>
    </header>
</template>
  
<script>
import { useAuthStore } from '@/stores/auth'

export default {
    name: 'DefaultLayout',
    computed: {
        isAuthenticated() {
            const authStore = useAuthStore()
            return authStore.isAuthenticated
        },
        isAdmin() {
            const authStore = useAuthStore()
            return authStore.isAdmin
        }
    }
}
</script>
  
<style scoped>
.header {
    background: #2c3e50;
    color: white;
    padding: 1rem;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.logo a {
    color: white;
    text-decoration: none;
    font-size: 1.5rem;
    font-weight: bold;
}

.nav-links {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.nav-links a {
    color: white;
    text-decoration: none;
}

.nav-links a:hover {
    text-decoration: underline;
}
</style>