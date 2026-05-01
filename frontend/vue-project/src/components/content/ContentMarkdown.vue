<template>
    <div class="content-markdown">
        <div class="content-markdown__content" v-html="renderedHtml"></div>
    </div>
</template>

<script>
import { marked } from 'marked'

export default {
    name: 'ContentMarkdown',
    props: {
        content: {
            type: String,
            default: ''
        },
        filename: {
            type: String,
            default: ''
        },
        originalFilename: {
            type: String,
            default: 'Документ'
        },
        fileUrl: {
            type: String,
            default: ''
        }
    },
    computed: {
        renderedHtml() {
            if (!this.content) return '<p>Нет содержимого</p>'
            return marked(this.content)
        }
    }
}
</script>

<style scoped>
.content-markdown {
    margin: 1rem 0;
}

.content-markdown__content {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    line-height: 1.6;
}

.content-markdown__content :deep(h1) {
    font-size: 1.75rem;
    margin-bottom: 1rem;
}

.content-markdown__content :deep(h2) {
    font-size: 1.5rem;
    margin: 1.5rem 0 1rem;
}

.content-markdown__content :deep(h3) {
    font-size: 1.25rem;
    margin: 1rem 0 0.75rem;
}

.content-markdown__content :deep(p) {
    margin-bottom: 1rem;
}

.content-markdown__content :deep(ul), 
.content-markdown__content :deep(ol) {
    margin-left: 1.5rem;
    margin-bottom: 1rem;
}

.content-markdown__content :deep(code) {
    background: #e9ecef;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: monospace;
}

.content-markdown__content :deep(pre) {
    background: #2c3e50;
    color: white;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin-bottom: 1rem;
}

.content-markdown__content :deep(pre code) {
    background: none;
    padding: 0;
}

.content-markdown__content :deep(img) {
    max-width: 100%;
    border-radius: 8px;
}

.content-markdown__content :deep(a) {
    color: #3498db;
    text-decoration: none;
}

.content-markdown__content :deep(a:hover) {
    text-decoration: underline;
}

.content-markdown__info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.content-markdown__filename {
    font-size: 0.875rem;
    color: #6c757d;
}
</style>