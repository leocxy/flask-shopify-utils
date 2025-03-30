import {createRouter, createWebHistory} from 'vue-router'
import IndexVue from '../views/Index.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        // extension routes
        // {
        //     path: '/func/payment-customization/create',
        //     name: 'payment.create',
        //     component: () => import('../extensions/PaymentCustomization.vue')
        // },
        // {
        //     path: '/func/payment-customization/:record_id',
        //     name: 'payment.edit',
        //     component: () => import('../extensions/PaymentCustomization.vue'),
        //     props: true
        // },
        // {
        //     path: '/func/delivery-customization/create',
        //     name: 'delivery.create',
        //     component: () => import('../extensions/DeliveryCustomization.vue')
        // },
        // {
        //     path: '/func/delivery-customization/:record_id',
        //     name: 'delivery.edit',
        //     component: () => import('../extensions/DeliveryCustomization.vue'),
        //     props: true
        // },
        {path: '/', name: 'home', component: IndexVue},
        {path: '/:pathMatch(.*)*', name: 'not-found', component: IndexVue},
    ]
})

export default router
