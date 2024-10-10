import {ref} from "vue"
import {defineStore} from "pinia"
import isString from "lodash/isString"
import isUndefined from "lodash/isUndefined"
import Swal from "sweetalert2"

const Toast = Swal.mixin({
    toast: true,
    position: "bottom",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.onmouseenter = Swal.stopTimer;
        toast.onmouseleave = Swal.resumeTimer;
    }
})

export const useDefault = defineStore("default", () => {
    // https://pinia.vuejs.org/core-concepts/
    // https://masteringpinia.com/blog/how-to-create-private-state-in-stores
    const app_bridge = ref(window?.shopify ?? null)
    const internal_endpoints = [
        {name: 'check', url: '/admin/check'},
        {name: 'test_jwt', url: '/admin/test_jwt'},
        // add more endpoints here
        {name: 'product-discount', url: '/admin/product-discount'}
    ]

    const checkAppBridge = () => {
        if (app_bridge.value === null) {
            Toast.fire({
                icon: 'error',
                title: 'Error',
                text: 'App bridge is not available'
            })
        }
        return app_bridge.value !== null
    }

    const showToast = (message, payload = {}) => {
        payload = {
            ...{
                isError: false,
                title: null,
                duration: 3000
            }, ...payload
        }
        if (!checkAppBridge()) {
            Toast.fire({
                icon: payload.isError ? "error" : 'success',
                text: message,
                timer: payload.duration,
            })
        } else {
            app_bridge.value.toast.show(message, {
                duration: payload.duration,
                isError: payload.isError
            })
        }
    }

    const redirectAdmin = (resource, target = '_top') => {
        if (!checkAppBridge()) return
        open(`shopify://admin/${resource}`, target)
    }

    const redirectRemote = (url, target = '_blank') => {
        if (!checkAppBridge()) return
        open(url, target)
    }

    const productPicker = (payload) => {
        if (!checkAppBridge()) return
        payload = isUndefined(payload) ? {} : payload
        return app_bridge.value.resourcePicker({type: 'product', ...payload})
    }

    const variantPicker = (payload) => {
        if (!checkAppBridge()) return
        payload = isUndefined(payload) ? {} : payload
        return app_bridge.value.resourcePicker({type: 'variant', ...payload})
    }

    const collectionPicker = (payload) => {
        if (!checkAppBridge()) return
        payload = isUndefined(payload) ? {} : payload
        return app_bridge.value.resourcePicker({type: 'collection', ...payload})
    }

    const errorCallback = (err, isSaving) => {
        console.error(err)
        if (isSaving) setTimeout(() => isSaving.value = false, 1000)
        err = err?.data ?? err
        showToast(err?.message ? err.message : 'Oops... Something went wrong', {
            isError: true,
            title: 'Error',
            duration: 5000
        })
    }

    const formValidation = (schema, data, payload = null) => {
        try {
            let values = schema.validateSync(data, payload ?? {abortEarly: false, stripUnknown: true})
            return {rs: true, values, error: {}}
        } catch (err) {
            console.error('Validation fail', err.errors)
            let error = {}
            err.inner.forEach(v => error[v.path] = v.errors[0])
            return {rs: false, values: {}, error}
        }
    }

    const getApi = (name, params) => {
        let rs = internal_endpoints.find(v => v.name === name)
        rs = rs ? rs : {url: '/'}
        params = isUndefined(params) ? '' : '/' + (isString(params) ? params : params.join('/'))
        return `${rs.url}${params}`
    }


    return {
        app_bridge,
        checkAppBridge,
        showToast,
        redirectAdmin,
        redirectRemote,
        productPicker,
        variantPicker,
        collectionPicker,
        errorCallback,
        formValidation,
        getApi
    }
})