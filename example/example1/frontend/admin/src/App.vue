<template>
    <AppProvider>
        <Frame>
            <Page :title="title" :full-width="full_width">
                <RouterView @updateTitle="updateTitle" @setFullWidth="setFullWidth" />
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
import {useDefault} from "./stores/index"
// import {useRoute, useRouter} from "vue-router"

const $http = inject('$http')
const change = ref(false)
const title = ref('Vue3 App')
const full_width = ref(false)
const {success_toast, error_toast, getApi, errorCallback} = useDefault()
// const route = useRoute()
const checkAppScopes = () => {
    $http.get(getApi('check', 'status')).then(({data}) => change.value = data.data.change).catch(errorCallback)
}

const updateTitle = (val) => title.value = val

const setFullWidth = (val) => full_width.value = val

const updateScopes = () => {
    $http.get(getApi('check', 'reinstall')).then(({data}) => {
        data = data.data
        if (window.self === window.top) return window.location.href = data
        // redirectRemote(data)
    }).catch(err => errorCallback(err))
}

onMounted(() => {
    $http.defaults.headers.common['Authorization'] = `Bearer ${window?.AppInfo.jwtToken}`
    if (!window.shopify) {
        error_toast.content = 'Shopify App bridge does not initialize! Please open the page on Admin Panel.'
        error_toast.active = true
    } else {
        success_toast.content = 'Shopify App bridge initialized!'
        success_toast.active = true

    }
    // Check Update
    checkAppScopes()
})
</script>