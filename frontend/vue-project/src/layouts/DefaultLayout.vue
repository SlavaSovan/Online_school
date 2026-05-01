<template>
    <div class="layout">
        <AppHeader />
        <main class="main-content">
            <slot />
        </main>
        <AppFooter />
    </div>
</template>

<script>
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'

export default {
    name: 'DefaultLayout',
    components: {
        AppHeader,
        AppFooter
    }
}
</script>

<style scoped>
.layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.main-content {
    flex: 1;
    padding: 20px;
}
</style>