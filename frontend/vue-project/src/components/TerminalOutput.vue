<template>
    <div class="terminal-output">
        <div class="terminal-output__header">
            <span class="terminal-output__title">Вывод программы</span>
            <action-icon v-if="hasContent" variant="clear" @click="clear" title="Очистить" />
        </div>
        
        <!-- Загрузка -->
        <div v-if="loading" class="terminal-output__info">
            <i class="fas fa-spinner fa-pulse"></i>
            <p>Выполнение кода...</p>
        </div>
        
        <!-- Было выполнено и есть вывод -->
        <div v-else-if="hasOutput" class="terminal-output__content">
            <pre>{{ output }}</pre>
        </div>
        
        <!-- Было выполнено, вывод пустой (успешно) -->
        <div v-else-if="wasRun && !hasOutput && !hasError" class="terminal-output__content terminal-output__info">
            <i class="fas fa-check-circle"></i>
            <p>Программа выполнена успешно, вывод отсутствует</p>
        </div>
        
        <!-- Была ошибка -->
        <div v-if="hasError" class="terminal-output__content">
            <pre>{{ error }}</pre>
        </div>
        
        <!-- Код еще не запускался -->
        <div v-if="!wasRun && !hasError && !loading" class="terminal-output__info">
            <i class="fas fa-terminal"></i>
            <p>Запустите код, чтобы увидеть результат</p>
        </div>
    </div>
</template>

<script>
export default {
    name: 'TerminalOutput',
    props: {
        output: {
            type: String,
            default: ''
        },
        error: {
            type: String,
            default: ''
        },
        wasRun: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        hasOutput() {
            return this.output && this.output.trim() !== ''
        },
        hasError() {
            return this.error && this.error.trim() !== ''
        },
        hasContent() {
            return this.hasOutput || this.hasError
        }
    },
    methods: {
        clear() {
            this.$emit('clear')
        }
    },
    emits: ['clear'],
}
</script>

<style scoped>
.terminal-output {
    background: #0a0e12;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #2c3e50;
}

.terminal-output__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #2c3e50;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #3d566e;
}

.terminal-output__title {
    color: #3498db;
    font-size: 0.75rem;
    font-weight: 500;
}

.terminal-output__content {
    padding: 1rem;
}

.terminal-output__content pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 13px;
    background: #0a0e12;
    color: #f5f7fa;
    line-height: 1.4;
    white-space: pre-wrap;
    word-break: break-all;
}

.terminal-output__info {
    padding: 2rem;
    text-align: center;
    color: #7f8c8d;
}

.terminal-output__info i {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.terminal-output__info p {
    margin: 0;
    font-size: 0.875rem;
}
</style>