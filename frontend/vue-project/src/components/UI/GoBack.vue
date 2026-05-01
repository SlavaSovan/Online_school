<!-- components/GoBack.vue -->
<template>
    <button class="go-back" @click="$emit('click')">
        ← Назад
    </button>
</template>

<script>
export default {
    name: 'go-back-btn',
    emits: ['click']
}
</script>

<style scoped>
.go-back {
    background: none;
    border: none;
    color: #6c757d;
    cursor: pointer;
    transition: color 0.2s;
    display: inline-flex;
    align-items: center;
}

.go-back:hover {
    color: #3498db;
}
</style>