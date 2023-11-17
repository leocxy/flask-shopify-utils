<template>
    <Layout>
        <Card>
            <EmptyState v-bind="args">
                <p>Track and receive your incoming inventory from suppliers.</p>
                <template #footerContent>
                    <p>
                        If you don't want to add a transfer, you can import your inventory from
                        <Link monochrome url="/settings"> settings</Link>.
                    </p>
                </template>
            </EmptyState>
        </Card>
    </Layout>
</template>

<script setup>
import {ref, onMounted, inject} from 'vue'
import {useDefault} from "../stores/index"

const $http = inject('$http')
const {errorCallback, getApi, success_toast} = useDefault()
const isSaving = ref(false)


onMounted(() => {
    isSaving.value = true
    $http.get(getApi('test_jwt')).then(() => {
        isSaving.value = false
        success_toast.content = 'This should never work!'
        success_toast.active = true
    }).catch(err => errorCallback(err, isSaving))
})
</script>
