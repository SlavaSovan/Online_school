<template>
    <Transition name="toast">
        <div v-if="visible" class="toast" :class="`toast--${type}`">
            <div class="toast__icon">
                <span v-if="type === 'success'">✓</span>
                <span v-else-if="type === 'error'">✗</span>
                <span v-else-if="type === 'warning'">⚠</span>
                <span v-else>ℹ</span>
            </div>
            <div class="toast__content">
                <p class="toast__message">{{ message }}</p>
            </div>
            <button class="toast__close" @click="close">×</button>
        </div>
    </Transition>
</template>

<script>
export default {
    name: 'ToastNotification',
    data() {
        return {
            visible: false,
            message: '',
            type: 'info',
            timeout: null
        }
    },
    methods: {
        show(message, type = 'info', duration = 3000) {
            this.message = message
            this.type = type
            this.visible = true
            
            if (this.timeout) {
                clearTimeout(this.timeout)
            }
            
            this.timeout = setTimeout(() => {
                this.close()
            }, duration)
        },
        
        close() {
            this.visible = false
            if (this.timeout) {
                clearTimeout(this.timeout)
                this.timeout = null
            }
        }
    },
    beforeUnmount() {
        if (this.timeout) {
            clearTimeout(this.timeout)
        }
    }
}
</script>

<style scoped>
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    min-width: 280px;
    max-width: 400px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    z-index: 1000;
    border-left: 4px solid;
    pointer-events: auto;
}

.toast--success {
    border-left-color: #27ae60;
}

.toast--success .toast__icon {
    background: #27ae60;
}

.toast--error {
    border-left-color: #e74c3c;
}

.toast--error .toast__icon {
    background: #e74c3c;
}

.toast--warning {
    border-left-color: #f39c12;
}

.toast--warning .toast__icon {
    background: #f39c12;
}

.toast--info {
    border-left-color: #3498db;
}

.toast--info .toast__icon {
    background: #3498db;
}

.toast__icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 14px;
    font-weight: bold;
    flex-shrink: 0;
}

.toast__content {
    flex: 1;
}

.toast__message {
    margin: 0;
    font-size: 14px;
    color: #2c3e50;
    line-height: 1.4;
}

.toast__close {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #95a5a6;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
    flex-shrink: 0;
}

.toast__close:hover {
    background: #ecf0f1;
    color: #2c3e50;
}

/* Анимации */
.toast-enter-active,
.toast-leave-active {
    transition: all 0.3s ease;
}

.toast-enter-from {
    transform: translateX(100%);
    opacity: 0;
}

.toast-leave-to {
    transform: translateX(100%);
    opacity: 0;
}
</style>