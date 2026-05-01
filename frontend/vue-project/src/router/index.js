import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('@/views/HomeView.vue'),
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/LoginView.vue'),
            meta: { guestOnly: true },
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('@/views/RegisterView.vue'),
            meta: { guestOnly: true },
        },
        {
            path: '/profile',
            name: 'profile',
            component: () => import('@/views/ProfileView.vue'),
            meta: { requiresAuth: true },
        },
        {
            path: '/change-password',
            name: 'change-password',
            component: () => import('@/views/ChangePasswordView.vue'),
            meta: { requiresAuth: true },
        },
        {
            path: '/catalog',
            name: 'catalog',
            component: () => import('@/views/CatalogView.vue'),
        },
        {
            path: '/course/:slug',
            name: 'course',
            component: () => import('@/views/CourseView.vue'),
        },
        {
            path: '/my-courses',
            name: 'my-courses',
            component: () => import('@/views/MyCoursesView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/course/:courseSlug/module/:moduleSlug/lesson/:lessonSlug',
            name: 'lesson',
            component: () => import('@/views/LessonView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/course/create',
            name: 'course-create',
            component: () => import('@/views/CourseEditView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/course/:slug/edit',
            name: 'course-edit',
            component: () => import('@/views/CourseEditView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/course/:courseSlug/module/:moduleSlug/lesson/:lessonSlug/content',
            name: 'lesson-content-edit',
            component: () => import('@/views/LessonContentEditView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/course/:courseSlug/module/:moduleSlug/lesson/:lessonSlug/tasks',
            name: 'lesson-tasks-edit',
            component: () => import('@/views/LessonTasksEditView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/task/:taskId/test',
            name: 'test-task',
            component: () => import('@/views/TestTaskView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/task/:taskId/file',
            name: 'file-task',
            component: () => import('@/views/FileTaskView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/task/:taskId/sandbox',
            name: 'sandbox-task',
            component: () => import('@/views/SandboxTaskView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/mentoring/course/:courseSlug',
            name: 'mentor-course',
            component: () => import('@/views/MentorCourseView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/mentoring/course/:courseSlug/module/:moduleSlug/lesson/:lessonSlug/content',
            name: 'mentor-lesson-content',
            component: () => import('@/views/MentorLessonContentView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/mentoring/course/:courseSlug/module/:moduleSlug/lesson/:lessonSlug/task/:taskId',
            name: 'mentor-task',
            component: () => import('@/views/MentorTaskView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/admin',
            name: 'admin',
            component: () => import('@/views/AdminView.vue'),
            meta: { requiresAuth: true, requiresAdmin: true }
        },
    ],
})

router.beforeEach((to, from) => {
    const authStore = useAuthStore()
    const isLoggedIn = authStore.isAuthenticated
    
    if (to.meta.requiresAuth && !isLoggedIn) {
        next('/login')
    }
    
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
        return '/'
    }
    
    if (to.meta.guestOnly && isLoggedIn) {
        return '/'
    }
    
    return true
})

export default router
