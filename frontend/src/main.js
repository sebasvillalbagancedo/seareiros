import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/botones.css'
import './assets/formularios.css'
import './assets/main.css'
import './assets/mensajes.css'
import './assets/modal.css'
import './assets/modulos.css'
import './assets/sidebar.css'
import './assets/tablas.css'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')