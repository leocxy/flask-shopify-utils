import {createRouter, createWebHistory} from 'vue-router'
import IndexVue from '../views/Index.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {path: '/', name: 'home', component: IndexVue},
        {path: '/:pathMatch(.*)*', name: 'not-found', component: IndexVue},
    ]
})

export default router
