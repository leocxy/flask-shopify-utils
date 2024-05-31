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

export const useDefault = defineStore("default", {
    state: () => ({
        app_bridge: window?.shopify ?? null,
        // Add your internal endpoints here
        internal_endpoints: [
            {name: 'check', url: '/admin/check'},
            {name: 'test_jwt', url: '/admin/test_jwt'},
        ],
    }),
    actions: {
        showToast(message, payload = {}) {
            payload = {
                ...{
                    isError: false,
                    title: null,
                    duration: 3000
                }, ...payload
            }
            if (!this.checkAppBridge()) {
                Toast.fire({
                    icon: payload.isError ? "error" : 'success',
                    text: message,
                    timer: payload.duration,
                })
            } else {
                this.app_bridge.toast.show(message, {
                    duration: payload.duration,
                    isError: payload.isError
                })
            }
        },
        checkAppBridge() {
            if (this.app_bridge === null) {
                Toast.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'App bridge is not available'
                })
            }
            return this.app_bridge !== null
        },
        redirectAdmin(resource, target = '_top') {
            if (!this.checkAppBridge()) return
            open(`shopify://admin/${resource}`, target)
        },
        redirectRemote(url, target = '_blank') {
            if (!this.checkAppBridge()) return
            open(url, target)
        },
        productPicker(payload) {
            if (!this.checkAppBridge()) return
            payload = isUndefined(payload) ? {} : payload
            return this.app_bridge.resourcePicker({type: 'product', ...payload})
        },
        variantPicker(payload) {
            if (!this.checkAppBridge()) return
            payload = isUndefined(payload) ? {} : payload
            return this.app_bridge.resourcePicker({type: 'variant', ...payload})
        },
        collectionPicker(payload) {
            if (!this.checkAppBridge()) return
            payload = isUndefined(payload) ? {} : payload
            return this.app_bridge.resourcePicker({type: 'collection', ...payload})
        },
        errorCallback(err, isSaving) {
            console.error(err)
            if (isSaving) setTimeout(() => isSaving.value = false, 1000)
            err = err?.data ?? err
            this.showToast(err?.message ? err.message : 'Oops... Something went wrong', {
                isError: true,
                title: 'Error',
                duration: 5000
            })
        },
        formValidation(schema, data, payload = null) {
            try {
                let values = schema.validateSync(data, payload ?? {abortEarly: false, stripUnknown: true})
                return {rs: true, values, error: {}}
            } catch (err) {
                console.error('Validation fail', err.errors)
                let error = {}
                err.inner.forEach(v => error[v.path] = v.errors[0])
                return {rs: false, values: {}, error}
            }
        },
    },
    getters: {
        getApi(state) {
            return (name, params) => {
                let rs = state.internal_endpoints.find(v => v.name === name)
                rs = rs ? rs : {url: '/'}
                params = isUndefined(params) ? '' : '/' + (isString(params) ? params : params.join('/'))
                return `${rs.url}${params}`
            }
        }
    }
})