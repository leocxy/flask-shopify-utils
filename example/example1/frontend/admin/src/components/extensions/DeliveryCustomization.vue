<template>
    <Layout>
        <LayoutSection>
            <Card>
                <BlockStack gap="200">
                    <InlineGrid columns="1fr auto">
                        <Text as="h2" variant="headingSm">Delivery Customization</Text>
                        <ButtonGroup>
                            <Button tone="critical" variant="plain" :loading="isSaving" v-show="record_id"
                                    @click="deleteData">Delete
                            </Button>
                            <Button variant="plain" @click="saveData" :loading="isSaving">Save</Button>
                        </ButtonGroup>
                    </InlineGrid>
                    <TextField
                        label="Title"
                        v-model="form.title"
                        :error="errors?.title"
                        :disabled="isSaving"/>
                    <Checkbox
                        label="Active"
                        :loading="isSaving"
                        v-model="form.enabled"
                        :error="errors?.enabled"/>
                    <TextField
                        label="Cart Attribute Key"
                        v-model="form.attr_key"
                        disabled
                        help-text="Based on the cart attribute to determine which shipping methods should be hidden."
                        :error="errors?.attr_key" />
                </BlockStack>
            </Card>
        </LayoutSection>
        <LayoutSection variant="oneThird">
            <Card>
                <BlockStack gap="200">
                    <Text as="h2" variant="headingSm">Summary</Text>
                    <Text as="p">
                        Based on the cart attribute "<Text as="strong" tone="critical">{{ form.attr_key }}</Text>", show or hide specific shipping methods.
                    </Text>
                    <Text as="p">
                        when it equal to
                        <Text as="strong" tone="caution">"separate"</Text>,
                        all ship together methods will be hidden.
                    </Text>
                    <Text as="p">
                        when it equal to
                        <Text as="strong" tone="caution">"together"</Text>,
                        all ship separate methods will be hidden.
                    </Text>
                </BlockStack>
            </Card>
        </LayoutSection>
    </Layout>
    <PageActions>
        <template #primaryAction>
            <ButtonGroup>
                <Button :loading="isSaving" @click="toSettingPage">Cancel</Button>
                <Button variant="primary" tone="critical" :loading="isSaving" v-if="record_id" @click="deleteData">
                    Delete
                </Button>
                <Button variant="primary" :loading="isSaving" @click="saveData">Save</Button>
            </ButtonGroup>
        </template>
    </PageActions>
</template>

<script setup>
import {ref, inject, onMounted} from 'vue'
import {useRouter} from "vue-router"
import Swal from 'sweetalert2'
import * as Yup from 'yup'


const props = defineProps(['record_id'])
const $http = inject('$http')
const router = useRouter()
import {useDefault} from '../stores'

const store = useDefault()
const emit = defineEmits(['updateTitle', 'setFullWidth'])
const {getApi, redirectAdmin, errorCallback, showToast, formValidation} = store

const record_id = ref(props.record_id)
const errors = ref({})
const isSaving = ref(false)
const form = ref({
    title: null,
    enabled: false,
    attr_key: 'shipping-preference',
})
const formSchema = Yup.object().shape({
    title: Yup.string().required(),
    enabled: Yup.boolean().required(),
    // extra
    attr_key: Yup.string().required(),
})

const toSettingPage = () => redirectAdmin('settings/shipping')


const saveData = () => {
    const {rs, values, error} = formValidation(formSchema, form.value)
    if (!rs) {
        errors.value = error
        return
    }

    const param = record_id.value ? record_id.value.toString() : 'create'
    const url = getApi('delivery', param)

    isSaving.value = true
    $http.post(url, values).then(({data}) => {
        const action = record_id.value ? 'updated' : 'created'
        if (action === 'created') {
            record_id.value = data.id
            router.replace({name: 'delivery.edit', params: {record_id: data.id}})
        }
        showToast(`Delivery customization ${action} successfully!`)
        isSaving.value = false
    }).catch(err => errorCallback(err, isSaving))
}

const deleteData = () => {
    if (!record_id.value) return

    Swal.fire({
        title: 'Are you sure?',
        text: 'You will not be able to recover this action!',
        icon: 'warning',
        showCancelButton: true
    }).then(({isConfirmed}) => {
        if (!isConfirmed) return
        isSaving.value = true

        $http.delete(getApi('delivery', record_id.value.toString())).then(() => {
            showToast('Delivery customization deleted!')
            setTimeout(toSettingPage, 1500)
        }).catch(err => errorCallback(err, isSaving))
    })
}
const loadData = () => {
    isSaving.value = true
    $http.get(getApi('delivery', record_id.value.toString())).then(({data}) => {
        form.value = {...data}
        showToast('Delivery customization loaded!')
        isSaving.value = false
    })
}

onMounted(() => {
    emit('updateTitle', 'Delivery Customization')
    emit('setFullWidth', false)
    if (record_id.value) loadData()
})
</script>