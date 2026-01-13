<template>
    <Layout>
        <LayoutSection>
            <BlockStack gap="400">
                <Card>
                    <BlockStack gap="200">
                        <Text as="h2" variant="headingSm">Configuration</Text>
                        <FormLayout>
                            <TextField
                                label="Title"
                                :error="errors?.title"
                                v-model="form.title" :loading="isSaving"/>
                            <Checkbox
                                label="Active"
                                :error="errors?.enabled"
                                v-model="form.enabled" :loading="isSaving"/>
                            <TextField
                                label="Destination Country Code"
                                v-model="form.destination"
                                :error="errors?.destination" :loading="isSaving"/>
                        </FormLayout>
                    </BlockStack>
                </Card>
                <Card>
                    <BlockStack gap="200">
                        <InlineGrid columns="1fr auto">
                            <Text as="h2" variant="headingSm">Hide payment methods</Text>
                            <Button :loading="isSaving" variant="plain" @click="addMethod">Add</Button>
                        </InlineGrid>
                        <FormLayout>
                            <template v-for="(_, k) in form.methods" :key="k">
                                <TextField
                                    :label="` ${k + 1}. Payment method`"
                                    help-text="Name of the payment method"
                                    :error="dynamicMethodError(k)"
                                    v-model="form.methods[k]" :loading="isSaving">
                                    <template #connectedRight>
                                        <Button
                                            :loading="isSaving"
                                            @click="removeMethod(k)"
                                            variant="primary"
                                            tone="critical">
                                            Remove
                                        </Button>
                                    </template>
                                </TextField>
                            </template>
                        </FormLayout>
                        <InlineError :message="errors?.methods" />
                    </BlockStack>
                </Card>
            </BlockStack>
        </LayoutSection>
        <LayoutSection variant="oneThird">
            <Card>
                <BlockStack gap="200">
                    <Text as="h2" variant="headingSm">Summary</Text>
                    <Text as="p">
                        Description
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
    // extra
    destination: null,
    methods: [],
})
const formSchema = Yup.object().shape({
    title: Yup.string().required(),
    enabled: Yup.boolean().required(),
    // extra
    destination: Yup.string().required().oneOf(['NZ']),
    methods: Yup.array().of(Yup.string().required().max(255).min(3)).min(1),
})

const dynamicMethodError = (index) => {
    let key = `methods[${index}]`
    if (errors.value[key]) return errors.value[key]
}

const addMethod = () => form.value.methods.push(null)

const removeMethod = (index) => form.value.methods.splice(index, 1)

const toSettingPage = () => redirectAdmin('settings/payments')

const loadData = () => {
    isSaving.value = true
    $http.get(getApi('payment', record_id.value.toString())).then(({data}) => {
        form.value = {...data}
        isSaving.value = false
        showToast('Payment customization loaded data successfully')
    }).catch(err => errorCallback(err, isSaving))
}

const saveData = () => {
    const {rs, values, error} = formValidation(formSchema, form.value)
    if (!rs) {
        errors.value = error
        return
    }
    errors.value = {}

    isSaving.value = true
    const url = getApi('payment', record_id.value ? record_id.value.toString() : 'create')
    $http.post(url, values).then(({data}) => {
        let action = 'updated'
        if (!record_id.value) {
            record_id.value = data.id
            action = 'created'
            router.replace({name: 'payment.edit', params: {record_id: data.id}})
        }
        showToast(`Payment customization ${action} successfully!`)
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
        $http.delete(getApi('payment', record_id.value.toString())).then(() => {
            showToast('Payment Customization is deleted successfully.')
            setTimeout(() => toSettingPage(), 1000)
        }).catch(err => errorCallback(err, isSaving))
    })
}

onMounted(() => {
    emit('updateTitle', 'Payment Customization')
    emit('setFullWidth', false)
    if (record_id.value) loadData()
})
</script>