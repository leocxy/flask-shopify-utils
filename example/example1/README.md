### Introduction

The `backend` folder on the root will be the main backend web application. It created by `Flask` and `Flask-Shopify-Utils`.
The `frontend` folder on the root will be the frontend folders, currently, the Admin UI is created by `Vue3`.

The project is follow the [Shopify App Structure](https://shopify.dev/docs/apps/tools/cli/structure) guide.

### Environment

- OS: MacOX / Linux
- Python: >= 3.9
- VueJS: 3+

### Installation

You can use any package manager to install the dependencies, but we recommend using `yarn`.

```shell
# Install the Shopify CLI
>yarn add @shopify/cli

# Connect to the existing Shopify App
>yarn shopify app config link
# above command will creates the `shopify.app.toml` on the root folder, you might need to add the `SCOPES` to the file manually.

# generated the `.env` file on the root folder
>yarn shopify app env pull
# then you can add the `backend` config to the `.env` file
```

### Extensions

Function APIs are versioned. 
Updates are released quarterly and supported API versions are listed in the release notes. 
You can update to a new version of a Function API by completing the following steps.

1. Update the version of the API specified in your "shopify.extension.toml" file.
2. [Generate the latest schema](https://shopify.dev/docs/apps/build/functions/input-output#generating-the-latest-schema).

```shell
# example1: generate the schema
yarn app function schema --stdout --path=extensions/order-discount

# example2: generate the schema to the file
yarn app function schema --path=extensions/order-discount
```

### Download the example codes

After install the `flask-shopify-utils`, we can get the sample codes by running the following command on the root folder.

`Important Note` - It will overwrite the existing files, please make sure your work have been saved.

```shell
>lazy-dog
```

### Known issues

When you try to generate the extension by shopify CLI, it might popup an error message like 

```text
── external error ─────────────────────────────────────────────────────────────────────────────────────────────────────

Error coming from `npm exec -- graphql-code-generator --config package.json`

Command failed with exit code 1: npm exec -- graphql-code-generator --config package.json
Cannot convert undefined or null to object
[15:13:34] Parse configuration [started]
[15:13:34] Parse configuration [failed]
[15:13:34] → Cannot convert undefined or null to object

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

In this case, you can add `@shopify/shopify_function` and `javy` to the root` `package.json` file, like this:

```json
{
  "dependencies": {
    ...
    "@shopify/shopify_function": "^1.0.6",
    "javy": "0.1.2"
  }
}
```

Then try to generate the extension again.

Here is the [reference](https://github.com/Shopify/cli/issues/2095)