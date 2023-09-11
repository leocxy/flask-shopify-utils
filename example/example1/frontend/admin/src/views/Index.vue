<template>
    <Layout>
        <Card>
            <EmptyState v-bind="args">
                <p>Track and receive your incoming inventory from suppliers.</p>
                <template #footerContent>
                    <p>
                        If you don't want to add a transfer, you can import your inventory from
                        <Link monochrome url="/settings"> settings</Link>
                        .
                    </p>
                </template>
            </EmptyState>
        </Card>
    </Layout>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {storeToRefs} from "pinia"
import {useDefault} from "../stores/index"

const $http = inject('$http')
const store = useDefault()
const isSaving = ref(false)
const {success_toast} = storeToRefs(store)


onMounted(() => {
    isSaving.value = true
    $http.get(store.getApi('test_jwt')).then(() => {
        isSaving.value = false
        success_toast.active = true
        success_toast.content = 'This should never work!'
    }).catch(store.errorCallback)
})
</script>
