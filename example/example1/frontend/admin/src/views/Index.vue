<template>
    <Layout sectioned>
        <LegacyCard sectioned>
            <EmptyState
                heading="Example Empty State"
                image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png">
            </EmptyState>
        </LegacyCard>
    </Layout>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {useRouter} from 'vue-router'
import {useDefault} from '../stores/index'

const $http = inject('$http')
const router = useRouter()
const store = useDefault()
const {errorCallback, getApi, showToast} = store
const isSaving = ref(false)


onMounted(() => {
    isSaving.value = true
    $http.get(getApi('test_jwt')).then(() => {
        isSaving.value = false
        showToast('The test JWT is working!')
    }).catch(err => errorCallback(err, isSaving))
})
</script>
