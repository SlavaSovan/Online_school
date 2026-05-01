<template>
    <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">{{ title }}</h3>
                <button class="modal-close" @click="close">&times;</button>
            </div>
            <div class="modal-body">
                <slot></slot>
            </div>
            <div class="modal-footer">
                <base-button variant="primary" @click="confirm">{{ confirmText }}</base-button>
                <base-button variant="secondary" @click="close">Отмена</base-button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Modal',
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        title: {
            type: String,
            default: ''
        },
        confirmText: {
            type: String,
            default: 'Сохранить'
        }
    },
    emits: ['close', 'confirm'],
    methods: {
        close() {
            this.$emit('close')
        },
        confirm() {
            this.$emit('confirm')
        }
    }
}
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e9ecef;
}

.modal-title {
    margin: 0;
    font-size: 1.25rem;
    color: #2c3e50;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #7f8c8d;
}

.modal-close:hover {
    color: #e74c3c;
}

.modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 2rem;
    padding: 1rem 1.5rem;
    border-top: 1px solid #e9ecef;
}
</style>