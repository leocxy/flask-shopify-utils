import {fileURLToPath, URL} from 'node:url'
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

const host = process.env.HOST
    ? process.env.HOST.replace(/https?:\/\//, "")
    : "localhost";

const backend_api = `http://127.0.0.1:${process.env.BACKEND_PORT || 5000}`

let hmrConfig;
if (host === "localhost") {
    hmrConfig = {
        protocol: "ws",
        host: "localhost",
        port: 64999,
        clientPort: 64999,
    };
} else {
    hmrConfig = {
        protocol: "wss",
        host: host,
        port: process.env.FRONTEND_PORT,
        clientPort: 443,
    };
}


// https://vitejs.dev/config/
export default defineConfig({
    envDir: '../../',
    envPrefix: 'SHOPIFY_API_KEY',
    plugins: [
        vue(),
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
        proxy: {
            '/admin': backend_api,
            '/callback': backend_api,
            '^/assets/.*': {
                target: backend_api,
                rewrite: (path) => path.replace(/^\/assets/, '/admin/assets'),
            },
            '^/proxy/.*': {
                target: backend_api,
                rewrite: (path) => path.replace(/^\/proxy/, ''),
            },
        },
    },
    base: process.env.npm_lifecycle_event.includes('build') ? '/admin' : '/',
    build: {
        outDir: '../../dist/admin',
        emptyOutDir: true,
    }
})
