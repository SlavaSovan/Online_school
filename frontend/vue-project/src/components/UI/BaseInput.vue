<template>
    <div class="input-group">
        <label v-if="label">{{ label }}</label>
        <input 
            :type="type"
            :value="modelValue"
            :placeholder="placeholder"
            :disabled="disabled"
            @input="$emit('update:modelValue', $event.target.value)"
        />
        <span v-if="error" class="error-hint">{{ error }}</span>
        <span v-else-if="hint" class="hint">{{ hint }}</span>
    </div>
</template>

<script>
export default {
    name: 'base-input',
    props: {
        modelValue: [String, Number],
        label: String,
        type: {
            type: String,
            default: 'text'
        },
        placeholder: String,
        disabled: {
            type: Boolean,
            default: false
        },
        error: String,
        hint: String
    },
    emits: ['update:modelValue']
}
</script>

<style scoped>
.input-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

input {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
}

input:focus {
    outline: none;
    border-color: #3498db;
}
</style>