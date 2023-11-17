import {defineStore} from "pinia"
import isString from "lodash/isString"
import isUndefined from "lodash/isUndefined"

export const useDefault = defineStore("default", {
    state: () => ({
        app_bridge: window?.shopify || null,
        success_toast: {
            active: false,
            content: 'Success',
            duration: 3000,
        },
        error_toast: {
            active: false,
            content: 'Error',
            duration: 5000,
        },
        // Add your internal endpoints here
        internal_endpoints: [
            {name: 'check', url: '/admin/check'},
            {name: 'test_jwt', url: '/admin/test_jwt'},
        ],
    }),
    actions: {

        checkAppBridge() {
            if (this.app_bridge === null) {
                this.error_toast.content = 'App bridge is not available'
                this.error_toast.active = true
                return false
            }
            return true
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
            err = err?.data || err
            this.error_toast.active = true
            this.error_toast.content = err?.message ? err.message : 'Oops... Something went wrong'
        }
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