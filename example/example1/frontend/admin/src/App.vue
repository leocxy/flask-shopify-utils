<template>
    <AppProvider>
        <Page :title="title" :full-width="full_width">
            <RouterView @updateTitle="updateTitle" @setFullWidth="setFullWidth"/>
            <FooterHelp v-show="change">
                <Link @click="updateScopes">Update</Link>
                app scopes to get full functionality.
            </FooterHelp>
        </Page>
    </AppProvider>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {useDefault} from "./stores/index"
import {useRoute, useRouter} from "vue-router"

const $http = inject('$http')
const change = ref(false)
const title = ref('PS x Mr Ralph')
const full_width = ref(false)
const {getApi, errorCallback, showToast} = useDefault()
const route = useRoute()
const router = useRouter()
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
        showToast('Shopify App bridge does not initialize! Please open the page on Admin Panel.', {isError: true})
    } else {
        showToast('Shopify App bridge initialized!')
    }
    // Check Update
    checkAppScopes()
})
</script>