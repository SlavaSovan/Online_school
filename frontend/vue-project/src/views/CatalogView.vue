<template>
    <div class="catalog">
        <h1 class="catalog__title">Каталог курсов</h1>
        
        <!-- Фильтры -->
        <div class="filters">
            <div class="filters__row">
                <base-input
                    v-model="filters.search"
                    placeholder="Поиск курсов..."
                    class="filters__search"
                    @input="onFilterChange"
                />
                
                <base-select
                    v-model="filters.category"
                    :options="categoryOptions"
                    placeholder="Все категории"
                    class="filters__select"
                    @update:modelValue="onFilterChange"
                />
                
                <base-select
                    v-model="filters.ordering"
                    :options="orderingOptions"
                    placeholder="Сортировка"
                    class="filters__select"
                    @update:modelValue="onFilterChange"
                />
                
                <base-checkbox
                    v-model="filters.free_only"
                    label="Только бесплатные"
                    @update:modelValue="onFilterChange"
                />
            </div>
        </div>
        
        <!-- Список курсов -->
        <div v-if="loading && courses.length === 0" class="catalog__loading">
            Загрузка...
        </div>
        
        <div v-else-if="error" class="catalog__error">
            {{ error }}
        </div>
        
        <div v-else class="courses-grid">
            <course-card
                v-for="course in courses"
                :key="course.id"
                :course="course"
                @click="goToCourse(course.slug)"
            />
        </div>
        
        <!-- Индикатор загрузки следующих страниц -->
        <div v-if="loadingMore" class="catalog__loading-more">
            Загрузка еще...
        </div>
        
        <!-- Триггер для бесконечной прокрутки -->
        <div ref="sentinel" class="catalog__sentinel"></div>
        
        <div v-if="!hasMore && courses.length > 0" class="catalog__end">
            Вы просмотрели все курсы
        </div>
    </div>
</template>

<script>
import { coursesApi } from '@/api/endpoints/courses'
import { categoriesApi } from '@/api/endpoints/categories'
import CourseCard from '@/components/CourseCard.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'

export default {
    name: 'CatalogView',
    components: { CourseCard },
    data() {
        return {
            courses: [],
            loading: false,
            loadingMore: false,
            error: null,
            filters: {
                search: '',
                category: '',
                ordering: '',
                free_only: false
            },
            cursor: null,
            hasMore: true,
            categories: [],
            categoryOptions: [],
            orderingOptions: [
                { value: '', label: 'По умолчанию' },
                { value: '-created_at', label: 'Сначала новые' },
                { value: 'created_at', label: 'Сначала старые' },
                { value: 'price', label: 'Сначала дешевые' },
                { value: '-price', label: 'Сначала дорогие' }
            ]
        }
    },
    async mounted() {
        await this.loadCategories()
        await this.loadCourses(true)
        this.setupInfiniteScroll()
    },
    beforeUnmount() {
        if (this.destroyScroll) {
            this.destroyScroll()
        }
    },
    methods: {
        async loadCategories() {
            try {
                const response = await categoriesApi.getCategories()
                this.categories = response.results || []
                this.categoryOptions = this.categories.map(cat => ({
                    value: cat.slug,
                    label: cat.name
                }))
            } catch (err) {
                console.error('Failed to load categories:', err)
            }
        },
        
        async loadCourses(reset = false) {
            if (reset) {
                this.loading = true
                this.courses = []
                this.cursor = null
                this.hasMore = true
            } else {
                this.loadingMore = true
            }
            
            try {
                const params = {
                    ...this.filters,
                    page_size: 20
                }
                
                if (this.cursor) {
                    params.cursor = this.cursor
                }
                
                // Убираем пустые значения
                Object.keys(params).forEach(key => {
                    if (params[key] === '' || params[key] === null || params[key] === undefined) {
                        delete params[key]
                    }
                })
                
                const response = await coursesApi.getCourses(params)
                
                if (reset) {
                    this.courses = response.results || []
                } else {
                    this.courses = [...this.courses, ...(response.results || [])]
                }
                
                this.cursor = response.next ? this.extractCursor(response.next) : null
                this.hasMore = !!response.next
                
                this.error = null
            } catch (err) {
                console.error('Failed to load courses:', err)
                this.error = 'Не удалось загрузить курсы'
            } finally {
                this.loading = false
                this.loadingMore = false
            }
        },
        
        extractCursor(url) {
            if (!url) return null
            const match = url.match(/cursor=([^&]+)/)
            return match ? match[1] : null
        },
        
        onFilterChange() {
            this.loadCourses(true)
        },
        
        async loadMore() {
            if (this.hasMore && !this.loading && !this.loadingMore) {
                await this.loadCourses(false)
                return true
            }
            return false
        },
        
        setupInfiniteScroll() {
            const sentinel = this.$refs.sentinel
            if (!sentinel) return
            
            const { initObserver, destroyObserver } = useInfiniteScroll(
                () => this.loadMore(),
                { threshold: 100 }
            )
            
            this.destroyScroll = destroyObserver
            initObserver(sentinel)
        },
        
        goToCourse(slug) {
            this.$router.push({ name: 'course', params: { slug } })
        }
    }
}
</script>

<style scoped>
.catalog {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

.catalog__title {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #2c3e50;
}

.filters {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filters__row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-end;
}

.filters__search {
    flex: 2;
    min-width: 200px;
}

.filters__select {
    flex: 1;
    min-width: 150px;
}

.courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
}

.catalog__loading,
.catalog__error {
    text-align: center;
    padding: 3rem;
    font-size: 1.125rem;
}

.catalog__error {
    color: #e74c3c;
}

.catalog__loading-more {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}

.catalog__sentinel {
    height: 20px;
    width: 100%;
}

.catalog__end {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}

@media (max-width: 768px) {
    .filters__row {
        flex-direction: column;
    }
    
    .filters__search,
    .filters__select {
        width: 100%;
    }
    
    .courses-grid {
        grid-template-columns: 1fr;
    }
}
</style>