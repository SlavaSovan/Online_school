<template>
    <button
        :type="type"
        :disabled="disabled"
        class="btn"
        :class="btnClass"
        @click="$emit('click')"
    >
        <slot>Кнопка</slot>
    </button>
</template>
  
<script>
export default {
    name: 'base-button',
    props: {
        type: {
            type: String,
            default: 'button'
        },
        disabled: {
            type: Boolean,
            default: false
        },
        variant: {
            type: String,
            default: 'primary',
            validator: (value) => ['primary', 'secondary', 'danger', 'success', 'add'].includes(value)
        }
    },
    emits: ['click'],
    computed: {
        btnClass() {
            return {
                'btn-primary': this.variant === 'primary',
                'btn-secondary': this.variant === 'secondary',
                'btn-danger': this.variant === 'danger',
                'btn-success': this.variant === 'success',
                'btn-add': this.variant === 'add',
            }
        }
    }
}
</script>
  
<style scoped>
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #2980b9;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover:not(:disabled) {
    background: #7f8c8d;
}

.btn-danger {
    background: #e74c3c;
    color: white;
}

.btn-danger:hover:not(:disabled) {
    background: #c0392b;
}

.btn-success {
    background: #27ae60;
    color: white;
}

.btn-success:hover:not(:disabled) {
    background: #219a52;
}

.btn-add {
    width: 100%;
    background: none;
    border: 1px dashed #3498db;
    color: #3498db;
}

.btn-add:hover:not(:disabled) {
    background: #3498db;
    color: white;
    border: 1px solid #3498db;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>