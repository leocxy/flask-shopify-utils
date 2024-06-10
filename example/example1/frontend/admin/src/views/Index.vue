<template>
    <Layout sectioned>
        <LegacyCard sectioned>
            <EmptyState
                heading="Manage your inventory transfers"
                :action="{ content: 'Add transfer' }"
                :secondary-action="{ content: 'Learn more', url: 'https://help.shopify.com' }"
                image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
            >
                <p>Track and receive your incoming inventory from suppliers.</p>
            </EmptyState>
        </LegacyCard>
    </Layout>
</template>

<script setup>
import {inject} from 'vue'
import {useDefault} from "../stores/index"

const $http = inject('$http')
const {errorCallback, getApi} = useDefault()
</script>
