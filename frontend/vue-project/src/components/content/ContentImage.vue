<template>
    <div class="content-image">
        <img 
            :src="fileUrl" 
            :alt="originalFilename"
            class="content-image__img"
            @click="openModal"
        />
        
        <!-- Модальное окно для просмотра -->
        <div v-if="showModal" class="content-image__modal" @click="closeModal">
            <img :src="fileUrl" :alt="originalFilename" class="content-image__modal-img" />
        </div>
    </div>
</template>

<script>
export default {
    name: 'ContentImage',
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
            default: 'Изображение'
        }
    },
    data() {
        return {
            showModal: false
        }
    },
    methods: {
        openModal() {
            this.showModal = true
        },
        closeModal() {
            this.showModal = false
        },
    }
}
</script>

<style scoped>
.content-image {
    margin: 1rem 0;
}

.content-image__img {
    max-width: 100%;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s;
}

.content-image__img:hover {
    transform: scale(1.02);
}

.content-image__info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.content-image__filename {
    font-size: 0.875rem;
    color: #6c757d;
}

.content-image__modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    cursor: pointer;
}

.content-image__modal-img {
    max-width: 90%;
    max-height: 90%;
    object-fit: contain;
}
</style>