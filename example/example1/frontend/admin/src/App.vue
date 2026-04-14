<template>
    <AppProvider :i18n="locales">
        <Page :title="title" :full-width="full_width">
            <RouterView @updateTitle="updateTitle" @setFullWidth="setFullWidth"/>
        </Page>
    </AppProvider>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {useDefault} from "./stores/index"
// import {useRoute, useRouter} from "vue-router"
import locales from '@ownego/polaris-vue/dist/locales/en.json'

const $http = inject('$http')
const store = useDefault()
const title = ref('Example')
const full_width = ref(false)
const {getApi, errorCallback, showToast, redirectRemote} = store
// const route = useRoute()
// const router = useRouter()

const updateTitle = (val) => title.value = val

const setFullWidth = (val) => full_width.value = val

const checkToken = () => {
    $http.get(getApi('check', 'reinstall')).then(({data}) => {
        if (data?.url) redirectRemote(data, '_top')
    }).catch(err => errorCallback(err))
}

onMounted(() => {
    if (!window.shopify) {
        showToast('Shopify App bridge does not initialize! Please open the page on Admin Panel.', {isError: true})
    } else {
        showToast('Shopify App bridge initialized!')
    }
    // Check AccessToken
    checkToken()
})
</script>
