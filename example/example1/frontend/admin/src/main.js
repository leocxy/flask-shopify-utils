import {createApp} from 'vue'
import {createPinia} from 'pinia'
import router from './router'
import Axios from 'axios'
import PolarisVue from "@ownego/polaris-vue"
import '@ownego/polaris-vue/dist/style.css'
// initial the SPA
import App from './App.vue'
const app = createApp(App)
// initial the plugins
app.use(createPinia())
app.use(router)
app.use(PolarisVue)
// You can use sweetalert2 directly in vue3

// global properties -> https://stackoverflow.com/questions/63100658/add-global-variable-in-vue-js-3
// initial the Axios
Axios.interceptors.request.use(async function (config) {
		// check Shopify App bridge
		if (!window?.shopify?.idToken) return config

		let session_token = await window?.shopify?.idToken()
		config.headers.Authorization = `Bearer ${session_token}`
		return config
	},
	function (error) {
		return Promise.reject(error);
	})
Axios.interceptors.response.use(function (response) {
	if (response.status === 200 && response.data instanceof Blob) return response
	// Deprecated - initial the admin JWT, use Shopify session token
	// https://shopify.dev/docs/apps/build/authentication-authorization/session-tokens/set-up-session-tokens
	// if (response.data?.jwtToken) Axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.jwtToken}`
	if (response.data.status !== 0) return Promise.reject(response)
	return response.data
}, function (error) {
	return Promise.reject(error)
})
app.provide('$http', Axios)
// mount the SPA
app.mount('#app')
