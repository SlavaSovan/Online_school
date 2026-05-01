import { createApp } from 'vue'
import ToastNotification from '@/components/ToastNotification.vue'

let toastInstance = null
let toastApp = null

export function useToast() {
    if (!toastInstance) {
        // Создаем контейнер для тоста
        const container = document.createElement('div')
        document.body.appendChild(container)
        
        toastApp = createApp(ToastNotification)
        toastInstance = toastApp.mount(container)
    }
    
    return {
        show(message, type = 'info', duration = 3000) {
            toastInstance.show(message, type, duration)
        },
        success(message, duration = 3000) {
            toastInstance.show(message, 'success', duration)
        },
        error(message, duration = 3000) {
            toastInstance.show(message, 'error', duration)
        },
        warning(message, duration = 3000) {
            toastInstance.show(message, 'warning', duration)
        },
        info(message, duration = 3000) {
            toastInstance.show(message, 'info', duration)
        }
    }
}