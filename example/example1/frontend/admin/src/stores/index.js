import {defineStore} from "pinia"
import {createApp} from "@shopify/app-bridge"
import {ResourcePicker, Redirect} from "@shopify/app-bridge/actions"
import isString from "lodash/isString"
import isUndefined from "lodash/isUndefined"

export const useDefault = defineStore("default", {
    state: () => ({
        app_bridge: null,
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
        setAppBridge(token, host) {
            this.app_bridge = createApp({
                apiKey: token,
                host: host,
            })
        },
        redirectAdmin(payload) {
            if (this.app_bridge === null) return false
            const redirect = Redirect.create(this.app_bridge);
            return redirect.dispatch(Redirect.Action.ADMIN_PATH, payload)
        },
        redirectRemote(payload) {
            if (this.app_bridge === null) return false
            const redirect = Redirect.create(this.app_bridge);
            return redirect.dispatch(Redirect.Action.REMOTE, {
                url: payload?.url || payload,
                newContext: payload?.newContext === undefined ? true : payload.newContext
            })
        },
        productPicker(payload) {
            if (this.app_bridge === null) return false
            const picker = ResourcePicker.create(this.app_bridge, {
                    options: {
                        showVariants: payload['showVariants'] || false,
                        selectMultiple: payload['selectMultiple'] || false,
                        initialSelectionIds: payload['initialSelectionIds'] || []
                    },
                    resourceType: ResourcePicker.ResourceType.Product
                }),
                cancel_cb = (payload && payload['cancel_cb'] && typeof payload['cancel_cb'] === 'function') ? payload['cancel_cb'] : () => {
                    picker.unsubscribe()
                },
                select_cb = (payload && payload['select_cb'] && typeof payload['select_cb'] === 'function') ? ({selection}) => {
                    payload['select_cb'](selection), picker.unsubscribe()
                } : () => {
                    picker.unsubscribe()
                };
            // selection callback
            picker.subscribe(ResourcePicker.Action.SELECT, select_cb);
            // cancel callback
            picker.subscribe(ResourcePicker.Action.CANCEL, cancel_cb);
            // dispatch picker
            picker.dispatch(ResourcePicker.Action.OPEN)
        },
        variantPicker(payload) {
            if (this.app_bridge === null) return false
            const picker = ResourcePicker.create(this.app_bridge, {
                    options: {
                        selectMultiple: payload['selectMultiple'] || false,
                        initialSelectionIds: payload['initialSelectionIds'] || []
                    },
                    resourceType: ResourcePicker.ResourceType.ProductVariant
                }),
                cancel_cb = (payload && payload['cancel_cb'] && typeof payload['cancel_cb'] === 'function') ? payload['cancel_cb'] : () => {
                    picker.unsubscribe()
                },
                select_cb = (payload && payload['select_cb'] && typeof payload['select_cb'] === 'function') ? ({selection}) => {
                    payload['select_cb'](selection), picker.unsubscribe()
                } : () => {
                    picker.unsubscribe()
                };
            // selection callback
            picker.subscribe(ResourcePicker.Action.SELECT, select_cb);
            // cancel callback
            picker.subscribe(ResourcePicker.Action.CANCEL, cancel_cb);
            // dispatch picker
            picker.dispatch(ResourcePicker.Action.OPEN)
        },
        collectionPicker(payload) {
            if (this.app_bridge === null) return false
            const picker = ResourcePicker.create(this.app_bridge, {
                    options: {showVariants: false, selectMultiple: payload['selectMultiple'] || false},
                    resourceType: ResourcePicker.ResourceType.Collection
                }),
                cancel_cb = (payload && payload['cancel_cb'] && typeof payload['cancel_cb'] === 'function') ? payload['cancel_cb'] : () => {
                    picker.unsubscribe()
                },
                select_cb = (payload && payload['select_cb'] && typeof payload['select_cb'] === 'function') ? ({selection}) => {
                    payload['select_cb'](selection), picker.unsubscribe()
                } : () => {
                    picker.unsubscribe()
                };
            // selection callback
            picker.subscribe(ResourcePicker.Action.SELECT, select_cb);
            // cancel callback
            picker.subscribe(ResourcePicker.Action.CANCEL, cancel_cb);
            // dispatch picker
            picker.dispatch(ResourcePicker.Action.OPEN)
        },
        errorCallback(err, isSaving) {
            console.error(err)
            if (isSaving) setTimeout(() => isSaving.value = false, 1000)
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