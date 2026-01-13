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
const store = useDefault()
const change = ref(false)
const title = ref('Example')
const full_width = ref(false)
const {getApi, errorCallback, showToast, redirectRemote} = store
const route = useRoute()
const router = useRouter()

const checkAppScopes = () => {
    $http.get(getApi('check', 'status')).then(({data}) => {
        if (data?.change !== undefined) return change.value = data.change
        return redirectRemote(data, '_top')
    }).catch(errorCallback)
}

const updateTitle = (val) => title.value = val

const setFullWidth = (val) => full_width.value = val

const updateScopes = () => {
    $http.get(getApi('check', 'reinstall')).then(({data}) => {
        redirectRemote(data, '_top')
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
