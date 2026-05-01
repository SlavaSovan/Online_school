<template>
    <div class="content-file">
        <div class="content-file__info">
            <div class="content-file__icon">
                <i :class="fileIcon"></i>
            </div>
            <div class="content-file__details">
                <div class="content-file__name">{{ originalFilename }}</div>
                <div class="content-file__meta">{{ formattedSize }}</div>
            </div>
            <base-button 
                variant="primary" 
                size="small"
                @click="downloadFile"
            >
                <i class="fas fa-download"></i>
                Скачать
            </base-button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ContentFile',
    props: {
        fileUrl: {
            type: String,
            required: true
        },
        filename: {
            type: String,
            default: ''
        },
        originalFilename: {
            type: String,
            default: 'Файл'
        },
        fileSize: {
            type: [String, Number],
            default: 0
        }
    },
    computed: {
        formattedSize() {
            if (!this.fileSize) return 'Размер неизвестен'
            const bytes = parseInt(this.fileSize)
            if (bytes < 1024) return `${bytes} B`
            if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
            return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
        },
        fileExtension() {
            if (!this.originalFilename) return ''
            const parts = this.originalFilename.split('.')
            return parts.length > 1 ? parts.pop().toLowerCase() : ''
        },
        fileIcon() {
            const extension = this.fileExtension
            
            // Markdown
            if (extension === 'md' || extension === 'markdown') {
                return 'fab fa-markdown'
            }
            
            // Images
            const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
            if (imageExts.includes(extension)) {
                return 'fas fa-file-image'
            }
            
            // Videos
            const videoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v']
            if (videoExts.includes(extension)) {
                return 'fas fa-file-video'
            }
            
            // Files (документы, архивы и т.д.)
            if (extension === 'pdf') {
                return 'fas fa-file-pdf'
            }
            if (extension === 'doc' || extension === 'docx') {
                return 'fas fa-file-word'
            }
            if (extension === 'xls' || extension === 'xlsx') {
                return 'fas fa-file-excel'
            }
            if (extension === 'ppt' || extension === 'pptx') {
                return 'fas fa-file-powerpoint'
            }
            if (extension === 'zip' || extension === 'rar') {
                return 'fas fa-file-archive'
            }
            if (extension === 'txt' || extension === 'rtf') {
                return 'fas fa-file-alt'
            }
            if (extension === 'csv') {
                return 'fas fa-file-csv'
            }
            if (extension === 'json') {
                return 'fas fa-file-code'
            }
            
            // По умолчанию
            return 'fas fa-file'
        }
    },
    methods: {
        downloadFile() {
            const link = document.createElement('a')
            link.href = this.fileUrl
            link.download = this.filename || this.originalFilename
            link.click()
        }
    }
}
</script>

<style scoped>
.content-file {
    margin: 1rem 0;
}

.content-file__info {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.content-file__icon {
    font-size: 2rem;
    width: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3498db;
}

.content-file__details {
    flex: 1;
}

.content-file__name {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 0.25rem;
    word-break: break-all;
}

.content-file__meta {
    font-size: 0.75rem;
    color: #6c757d;
}

.content-file__info .btn i {
    margin-right: 0.5rem;
}

/* Цвета для разных типов файлов */
.content-file__icon .fa-file-pdf {
    color: #e74c3c;
}

.content-file__icon .fa-file-word {
    color: #2980b9;
}

.content-file__icon .fa-file-excel {
    color: #27ae60;
}

.content-file__icon .fa-file-powerpoint {
    color: #e67e22;
}

.content-file__icon .fa-file-image {
    color: #9b59b6;
}

.content-file__icon .fa-file-video {
    color: #e74c3c;
}

.content-file__icon .fa-file-archive {
    color: #f39c12;
}

.content-file__icon .fa-file-code {
    color: #2c3e50;
}

.content-file__icon .fa-file-alt {
    color: #7f8c8d;
}

.content-file__icon .fa-file-csv {
    color: #2ecc71;
}

.content-file__icon .fa-markdown {
    color: #000;
}

@media (max-width: 768px) {
    .content-file__info {
        flex-wrap: wrap;
    }
    
    .content-file__icon {
        font-size: 1.5rem;
    }
    
    .content-file__info .btn {
        width: 100%;
        justify-content: center;
    }
}
</style>