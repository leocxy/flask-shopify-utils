<template>
    <AppProvider>
        <Frame>
            <Page :title="title" full-width>
                <RouterView @updateTitle="updateTitle"/>
                <FooterHelp v-show="change">
                    <Link @click="updateScopes">Update</Link>
                    app scopes to get full functionality.
                </FooterHelp>
                <Toast
                    v-if="success_toast.active"
                    :content="success_toast.content"
                    :duration="success_toast.duration"
                    @dismiss="success_toast.active = false"/>
                <Toast
                    v-if="error_toast.active"
                    :content="error_toast.content"
                    :duration="error_toast.duration"
                    :error="true"
                    :show-toast="error_toast.active = true"
                    @dismiss="error_toast.active = false"/>
            </Page>
        </Frame>
    </AppProvider>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {storeToRefs} from "pinia"
import {useDefault} from "./stores/index"

const $http = inject('$http')
const change = ref(false)
const title = ref('Vue3 App')
const store = useDefault()
const {success_toast, error_toast} = storeToRefs(store)
const checkAppScopes = () => {
    $http.get(store.getApi('check', 'status')).then(({data}) => change.value = data.data.change).catch(store.errorCallback)
}

const updateTitle = (val) => title.value = val

const updateScopes = () => {
    $http.get(store.getApi('check', 'reinstall')).then(({data}) => {
        data = data.data
        if (window.self === window.top) return window.location.href = data
        store.redirectRemote(data)
    }).catch(store.errorCallback)
}

onMounted(() => {
    let params = new URLSearchParams(window.location.search)
    let host = params.get('host'), shop = params.get('shop'), hmac = params.get('hmac'),
        timestamp = params.get('timestamp')
    let apiKey = window?.AppInfo?.apiKey
    // Render by Backend, Init App Bridge directly
    if (apiKey && apiKey !== '{{ apiKey }}' && host) {
        store.setAppBridge(apiKey, host)
        $http.defaults.headers.common['Authorization'] = `Bearer ${window?.AppInfo.jwtToken}`
    } else {
        if (shop && host && hmac && timestamp) {
            // App Bridge should not initial outside of Shopify admin panel
            if (window.self === window.top) {
                store.success_toast.active = true
                store.success_toast.content = 'Please open the app from Shopify admin panel!'
            } else {
                // AJAX Get jwtToken & apiKey for initial App Bridge
                $http.post(store.getApi('test_jwt'), {data: Object.fromEntries(params)}).then(({data}) => {
                    data = data.data
                    store.setAppBridge(data.apiKey, host)
                    $http.defaults.headers.common['Authorization'] = `Bearer ${data.jwtToken}`
                    store.success_toast.active = true
                    store.success_toast.content = 'App bridge initialized!'
                }).catch(store.errorCallback)
            }
        }
    }
    // Check Update
    checkAppScopes()
})
</script>