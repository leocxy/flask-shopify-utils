### Introduction

The `backend` folder on the root will be the main backend web application. It created by `Flask` and `Flask-Shopify-Utils`.
The `frontend` folder on the root will be the frontend folders, currently, the Admin UI is created by `Vue3`.

The project is follow the [Shopify App Structure](https://shopify.dev/docs/apps/tools/cli/structure) guide.

### Environment

- OS: MacOX / Linux
- Python: >= 3.9
- VueJS: 3+

### Installation

```shell
# Install the Shopify CLI
>yarn add @shopify/cli @shopify/app

# Connect to the existing Shopify App
>yarn shopify app config link
# above command will creates the `shopify.app.toml` on the root folder, you might need to add the `SCOPES` to the file manually.

# generated the `.env` file on the root folder
>yarn shopify app env pull
# then you can add the `backend` config to the `.env` file
```
