<template>
    <div class="file-upload" :class="{ 'file-upload--dragover': isDragover }">
        <input
            ref="fileInput"
            type="file"
            :accept="accept"
            class="file-upload__input"
            @change="handleFileChange"
        />
        <div 
            class="file-upload__area"
            @click="triggerFileInput"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
        >
            <div class="file-upload__icon">
                <i v-if="!selectedFile" class="fas fa-cloud-upload-alt"></i>
                <i v-else-if="uploading" class="fas fa-spinner fa-pulse"></i>
                <i v-else class="fas fa-check-circle"></i>
            </div>
            <div class="file-upload__text">
                <template v-if="!selectedFile">
                    <strong>Нажмите для выбора</strong> или перетащите файл сюда
                </template>
                <template v-else-if="uploading">
                    Загрузка...
                </template>
                <template v-else>
                    <strong>{{ selectedFile.name }}</strong>
                    <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
                </template>
            </div>
            <button 
                v-if="selectedFile && !uploading" 
                type="button" 
                class="file-upload__clear"
                @click.stop="clearFile"
            >
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div v-if="error" class="file-upload__error">
            {{ error }}
        </div>
    </div>
</template>

<script>
export default {
    name: 'file-upload',
    props: {
        accept: {
            type: String,
            default: '*/*'
        },
        uploading: {
            type: Boolean,
            default: false
        },
        error: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            isDragover: false,
            selectedFile: null
        }
    },
    watch: {
        uploading(val) {
            if (!val && this.selectedFile) {
                // После завершения загрузки очищаем выбранный файл
                this.clearFile()
            }
        }
    },
    methods: {
        triggerFileInput() {
            if (!this.uploading) {
                this.$refs.fileInput.click()
            }
        },
        
        handleFileChange(event) {
            const file = event.target.files[0]
            if (file) {
                this.selectedFile = file
                this.$emit('file-selected', file)
                this.$emit('update:error', '')
            }
        },
        
        onDragOver() {
            if (!this.uploading) {
                this.isDragover = true
            }
        },
        
        onDragLeave() {
            this.isDragover = false
        },
        
        onDrop(event) {
            this.isDragover = false
            if (this.uploading) return
            
            const file = event.dataTransfer.files[0]
            if (file) {
                this.selectedFile = file
                this.$emit('file-selected', file)
                this.$emit('update:error', '')
            }
        },
        
        clearFile() {
            this.selectedFile = null
            this.$refs.fileInput.value = ''
            this.$emit('file-cleared')
        },
        
        formatFileSize(bytes) {
            if (bytes < 1024) return `${bytes} B`
            if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
            return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
        },
        
        reset() {
            this.clearFile()
            this.isDragover = false
        }
    },
    emits: ['file-selected', 'file-cleared', 'update:error']
}
</script>

<style scoped>
.file-upload {
    width: 100%;
}

.file-upload__input {
    display: none;
}

.file-upload__area {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.file-upload__area:hover {
    border-color: #3498db;
    background: #e3f2fd;
}

.file-upload--dragover .file-upload__area {
    border-color: #27ae60;
    background: #e8f5e9;
}

.file-upload__icon {
    font-size: 1.5rem;
}

.file-upload__icon .fa-spinner {
    color: #f39c12;
}

.file-upload__icon .fa-check-circle {
    color: #27ae60;
}

.file-upload__text {
    flex: 1;
    color: #6c757d;
    font-size: 0.875rem;
}

.file-upload__text strong {
    color: #3498db;
}

.file-size {
    margin-left: 0.5rem;
    color: #95a5a6;
    font-size: 0.75rem;
}

.file-upload__clear {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: #e74c3c;
    padding: 0.25rem 0.5rem;
    border-radius: 50%;
    transition: all 0.2s;
}

.file-upload__clear:hover {
    background: #e74c3c;
    color: white;
}

.file-upload__error {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #e74c3c;
}

.file-upload__error i {
    margin-right: 0.25rem;
}
</style>