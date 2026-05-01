<template>
    <label class="base-checkbox">
        <input
            type="checkbox"
            :checked="modelValue"
            :disabled="disabled"
            @change="$emit('update:modelValue', $event.target.checked)"
        />
        <span class="base-checkbox__label">{{ label }}</span>
    </label>
</template>

<script>
export default {
    name: 'base-checkbox',
    props: {
        modelValue: Boolean,
        label: String,
        disabled: Boolean
    },
    emits: ['update:modelValue']
}
</script>

<style scoped>
.base-checkbox {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

.base-checkbox input {
    width: 1rem;
    height: 1rem;
    cursor: pointer;
}

.base-checkbox__label {
    font-size: 0.875rem;
    color: #2c3e50;
}
</style>