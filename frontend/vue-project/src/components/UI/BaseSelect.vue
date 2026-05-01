<template>
    <div class="base-select">
        <label v-if="label" class="base-select__label">{{ label }}</label>
        <select
            :value="modelValue"
            :disabled="disabled"
            class="base-select__field"
            @change="$emit('update:modelValue', $event.target.value)"
        >
            <option v-if="placeholder" value="">{{ placeholder }}</option>
            <option
                v-for="option in options"
                :key="option.value"
                :value="option.value"
            >
                {{ option.label }}
            </option>
        </select>
    </div>
</template>

<script>
export default {
    name: 'base-select',
    props: {
        modelValue: [String, Number],
        label: String,
        options: {
            type: Array,
            default: () => []
        },
        placeholder: String,
        disabled: Boolean
    },
    emits: ['update:modelValue']
}
</script>

<style scoped>
.base-select {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.base-select__label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #2c3e50;
}

.base-select__field {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 0.875rem;
    background: white;
    cursor: pointer;
}

.base-select__field:focus {
    outline: none;
    border-color: #3498db;
}
</style>