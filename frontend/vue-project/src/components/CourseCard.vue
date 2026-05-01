<template>
    <div class="course-card" @click="$emit('click')">
        <div class="course-card__content">
            <h3 class="course-card__title">{{ course.title }}</h3>
            <p class="course-card__description">{{ truncatedDescription }}</p>
            <div class="course-card__footer">
                <span class="course-card__lessons">Количество уроков: {{ course.lessons_count }}</span>
                <span class="course-card__price" :class="{ free: isFree }">
                    {{ isFree ? 'Бесплатно' : `${course.price} ₽` }}
                </span>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'course-card',
    props: {
        course: {
            type: Object,
            required: true
        }
    },
    computed: {
        truncatedDescription() {
            if (!this.course.description) return 'Описание отсутствует'
            if (this.course.description.length > 100) {
                return this.course.description.substring(0, 100) + '...'
            }
            return this.course.description
        },
        isFree() {
            return parseFloat(this.course.price) === 0
        }
    },
    emits: ['click']
}
</script>

<style scoped>
.course-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.course-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.course-card__title {
    font-size: 1.25rem;
    margin-bottom: 0.75rem;
    color: #2c3e50;
}

.course-card__description {
    color: #7f8c8d;
    line-height: 1.5;
    margin-bottom: 1rem;
}

.course-card__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}

.course-card__lessons {
    font-size: 0.875rem;
    color: #3498db;
}

.course-card__price {
    font-size: 1rem;
    font-weight: bold;
    color: #2c3e50;
}

.course-card__price.free {
    color: #27ae60;
}
</style>