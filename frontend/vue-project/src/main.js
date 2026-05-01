import '@fortawesome/fontawesome-free/css/all.min.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useToast } from '@/composables/useToast'

import "./assets/main.css"
import components from '@/components/UI'

const app = createApp(App)
const pinia = createPinia()

components.forEach(component => {
    app.component(component.name, component)
});


app.use(pinia)
app.use(router)

const authStore = useAuthStore()
authStore.initAuth()

app.config.globalProperties.$toast = useToast()

app.mount('#app')
