# Brief

This template should help get you started developing with Vue 3 in Vite.

The folder name is `frontend`, because we split the Frontend and Backend into two separate folders.
For us, the `frontend` folder should includes all the UI, such as the Admin UI.
The `backend` folder should includes all the server-side code.

For [Shopify app structure](https://shopify.dev/docs/apps/tools/cli/structure), the `frontend` is the service that accepts the HTTP requests.
It will created an tunnel via `ngrok` and forward the requests to the `frontend`.

In our case, the `ngrok` should forward the requests to our `backend` endpoint.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

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

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
yarn test:unit
```

### Run End-to-End Tests with [Playwright](https://playwright.dev)

```sh
# Install browsers for the first run
npx playwright install

# When testing on CI, must build the project first
yarn build

# Runs the end-to-end tests
yarn test:e2e
# Runs the tests only on Chromium
yarn test:e2e --project=chromium
# Runs the tests of a specific file
yarn test:e2e tests/example.spec.ts
# Runs the tests in debug mode
yarn test:e2e --debug
```

### Lint with [ESLint](https://eslint.org/)

```sh
yarn lint
```
