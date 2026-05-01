<template>
    <div class="code-editor">
        <div class="code-editor__toolbar">
            <span class="code-editor__language">Python</span>
        </div>
        <textarea
            ref="textarea"
            v-model="internalCode"
            class="code-editor__textarea"
            :disabled="disabled"
            spellcheck="false"
            @keydown="handleTab"
        ></textarea>
    </div>
</template>

<script>
export default {
    name: 'CodeEditor',
    props: {
        modelValue: {
            type: String,
            default: ''
        },
        disabled: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            internalCode: this.modelValue
        }
    },
    watch: {
        internalCode(val) {
            this.$emit('update:modelValue', val)
        },
        modelValue(val) {
            this.internalCode = val
        }
    },
    methods: {
        handleTab(event) {
            if (event.key === 'Tab') {
                event.preventDefault()
                const start = event.target.selectionStart
                const end = event.target.selectionEnd
                const value = this.internalCode
                this.internalCode = value.substring(0, start) + '    ' + value.substring(end)
                this.$nextTick(() => {
                    event.target.selectionStart = event.target.selectionEnd = start + 4
                })
            }
        }
    },
    emits: ['update:modelValue']
}
</script>

<style scoped>
.code-editor {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #2c3e50;
    background: #1e1e1e;
}

.code-editor__toolbar {
    background: #2c3e50;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #3d566e;
}

.code-editor__language {
    color: #3498db;
    font-size: 0.75rem;
    font-weight: 500;
}

.code-editor__textarea {
    width: 100%;
    min-height: 300px;
    background: #1e1e1e;
    color: #f5f7fa;
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.5;
    padding: 1rem;
    border: none;
    outline: none;
    resize: vertical;
}
</style>