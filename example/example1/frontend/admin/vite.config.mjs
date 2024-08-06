import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'


const proxyOptions = {
    target: `http://127.0.0.1:${process.env?.BACKEND_PORT ?? '5000'}`,
    changeOrigin: false,
    secure: true,
    ws: false
}

let proxy = {
    '^/admin(/|(\\?.*)?$)': proxyOptions
}
// yarn shopify app dev need proxy the extension to the backend server
if ((process.env.IS_PROXY || '0') === '1') {
    proxy['^/api(/|(\\?.*)?$)'] = proxyOptions
    proxy['^/(\\?.*)?$'] = proxyOptions
    proxy['/func'] = proxyOptions
}

const host = process.env.HOST
    ? process.env.HOST.replace(/https?:\/\//, '')
    : 'localhost'


let hmrConfig
if (host === 'localhost') {
    hmrConfig = {
        protocol: 'ws',
        host: 'localhost',
        port: 64999,
        clientPort: 64999
    }
} else {
    hmrConfig = {
        protocol: 'wss',
        host: host,
        port: process.env.FRONTEND_PORT,
        clientPort: 443
    }
}

export default defineConfig({
    envDir: '../../',
    envPrefix: 'SHOPIFY_API_KEY',
    plugins: [
        vue()
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        host: 'localhost',
        port: process.env.FRONTEND_PORT || 8080,
        hmr: hmrConfig,
        proxy
    },
    base: process.env.npm_lifecycle_event.includes('build') ? '/admin' : '/',
    build: {
        outDir: '../../dist/admin',
        emptyOutDir: true
    }
})
