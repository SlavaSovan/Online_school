<template>
    <div class="content-video">
        <video 
            :src="fileUrl"
            controls
            class="content-video__player"
        >
            Ваш браузер не поддерживает видео
        </video>
    </div>
</template>

<script>
export default {
    name: 'ContentVideo',
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
            default: 'Видео'
        }
    }
}
</script>

<style scoped>
.content-video {
    margin: 1rem 0;
}

.content-video__player {
    width: 100%;
    border-radius: 8px;
}

.content-video__info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.content-video__filename {
    font-size: 0.875rem;
    color: #6c757d;
}
</style>