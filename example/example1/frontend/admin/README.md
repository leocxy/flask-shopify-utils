## Brief

This template should help get you started developing with Vue 3 in Vite.

The folder name is `frontend`, because we split the Frontend and Backend into two separate folders.
For us, the `frontend` folder should includes all the UI, such as the Admin UI.
The `backend` folder should includes all the server-side code.

For [Shopify app structure](https://shopify.dev/docs/apps/tools/cli/structure), the `frontend` is the service that
accepts the HTTP requests.
It will created an tunnel via `ngrok` and forward the requests to the `frontend`.

In our case, the `ngrok` should forward the requests to our `backend` endpoint.


## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
yarn
```

### Compile and Hot-Reload for Development

```sh
yarn dev
```

### Compile and Minify for Production

```sh
yarn build
```

### Lint with [ESLint](https://eslint.org/)

```sh
yarn lint
```

### PyCharm or WebStorm Setup

For package "ownego/polaris-vue", It is working fine with PyCharm 2023.3.7.
There is an issue with the package "@ownego/polaris-vue" in PyCharm and WebStorm from version 2024.1 to 2025.2.

The IDEs are unable to resolve the types correctly, the Vue components are marked as unknown.
To fix this, we can

#### Step 1: Add a "tsconfig.json" to the "frontend/admin" folder

```json
{}
```

#### Step 2: Add a "globals.d.ts" to the "frontend/admin" folder

```ts
import "@ownego/polaris-vue/dist/volar"
```

JetBrains implemented the fix in 2025.3 version.
All we need to do is add a "tsconfig.json" to the "frontend/admin" folder.

```json
{
  "compilerOptions": {
    "types": [
      "@ownego/polaris-vue/dist/volar"
    ]
  }
}
```

[Reference](https://youtrack.jetbrains.com/issue/WEB-73178#focus=Comments-27-12690051.0-0)