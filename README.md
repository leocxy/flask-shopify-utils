# Flask-Shopify-Utils

[![Python 3.9](https://img.shields.io/github/actions/workflow/status/leocxy/flask-shopify-utils/CI.yml?branch=master&label=Python%203.9)](https://github.com/leocxy/flask-shopify-utils/actions/workflows/CI.yml?query=branch%3Amaster)
[![Python 3.10](https://img.shields.io/github/actions/workflow/status/leocxy/flask-shopify-utils/CI.yml?branch=master&label=Python%203.10)](https://github.com/leocxy/flask-shopify-utils/actions/workflows/CI.yml?query=branch%3Amaster)
[![Python 3.11](https://img.shields.io/github/actions/workflow/status/leocxy/flask-shopify-utils/CI.yml?branch=master&label=Python%203.11)](https://github.com/leocxy/flask-shopify-utils/actions/workflows/CI.yml?query=branch%3Amaster)
[![Python 3.12](https://img.shields.io/github/actions/workflow/status/leocxy/flask-shopify-utils/CI.yml?branch=master&label=Python%203.12)](https://github.com/leocxy/flask-shopify-utils/actions/workflows/CI.yml?query=branch%3Amaster)
[![Python 3.13](https://img.shields.io/github/actions/workflow/status/leocxy/flask-shopify-utils/CI.yml?branch=master&label=Python%203.13)](https://github.com/leocxy/flask-shopify-utils/actions/workflows/CI.yml?query=branch%3Amaster)

`flask-shopify-utils` is a Flask extension that provides common building blocks for Shopify custom apps: OAuth routes, HMAC and webhook validation, Shopify session-token checks, GDPR webhook routes, a GraphQL client, starter models, and a scaffold CLI.

- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Starter scaffold](#starter-scaffold)
- [Configuration](#configuration)
- [Route bundles](#route-bundles)
- [Authentication decorators](#authentication-decorators)
- [Models](#models)
- [GraphQL utilities](#graphql-utilities)
- [Development](#development)
- [License](#license)

## Features

- Shopify OAuth install and callback helpers for embedded custom apps.
- HMAC validation for OAuth callbacks, embedded-app entry points, app proxies, and webhooks.
- Shopify session-token validation through `check_session_jwt`.
- Optional default blueprints for app entry, admin reference endpoints, GDPR webhooks, and GraphQL schema generation.
- A retrying Shopify GraphQL client based on `sgqlc`.
- Starter SQLAlchemy models for stores and webhook jobs.
- `lazy-dog` CLI for copying the example scaffold into a new project.

## Installation

Install the package from PyPI:

```bash
pip install -U flask-shopify-utils
```

Or install with `uv`:

```bash
uv pip install -U flask-shopify-utils
```

The package supports Python 3.9 and newer.

## Quick start

Initialize Flask-SQLAlchemy before initializing `ShopifyUtil`. The extension reads the SQLAlchemy instance from `app.extensions['sqlalchemy']` during `init_app`.

```text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_shopify_utils import ShopifyUtil

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///shopify.db",
    SHOPIFY_API_KEY="your-shopify-api-key",
    SHOPIFY_API_SECRET="your-shopify-api-secret",
    SCOPES="read_products,write_products",
)

db = SQLAlchemy()
db.init_app(app)

shopify = ShopifyUtil()
shopify.init_app(app)

# Register only the route bundles your app needs.
shopify.enroll_default_route()
shopify.enroll_gdpr_route()
shopify.enroll_admin_route()
shopify.enroll_graphql_schema_cli()
```

If you use the bundled models, import them only after `ShopifyUtil().init_app(app)` has run:

```python
from flask_shopify_utils.model import Store, Webhook
```

See `example/` for complete sample projects.

## Starter scaffold

After installing the package, run `lazy-dog` in an empty project directory to copy the reference scaffold from `example/example1`:

```bash
lazy-dog
```

The command prompts before overwriting existing files or directories.

## Configuration

`ShopifyUtil.init_app()` sets defaults for the following Flask config values when they are not already configured:

| Key | Default | Purpose |
|---|---|---|
| `ROOT_PATH` | Current working directory | Base path for generated and temporary files. |
| `BACKEND_PATH` | `<ROOT_PATH>/backend` | Backend application path used by helpers. |
| `TEMPORARY_PATH` | `<BACKEND_PATH>/tmp` | Temporary output path. |
| `API_VERSION` | Latest supported Shopify API version | Shopify Admin API version used by GraphQL utilities. |
| `TIMEZONE` | `Pacific/Auckland` | Timezone for bundled model timestamps. |
| `SHOPIFY_API_SECRET` | `CUSTOM_APP_SECRET` | Shared secret for HMAC, webhook, and token validation. |
| `SHOPIFY_API_KEY` | `CUSTOM_APP_KEY` | Shopify app API key. |
| `BYPASS_VALIDATE` | `0` | Local-development validation bypass. Any non-zero integer is treated as the fake store id. |
| `DEBUG` | `False` | Flask debug flag fallback. |
| `SCOPES` | `read_products` | OAuth scopes requested during installation. |

Set `BYPASS_VALIDATE` to `0` in production.

## Route bundles

Routes are opt-in. Call the enrollment methods you need after `init_app()`.

| Method | Routes and behavior |
|---|---|
| `enroll_default_route()` | Registers `/`, `/admin`, `/install`, `/callback`, `/docs`, and a Shopify-aware `404` handler. |
| `enroll_gdpr_route()` | Registers `/webhook/shop/redact`, `/webhook/customers/redact`, and `/webhook/customers/data_request`; requests are verified with Shopify webhook HMAC. |
| `enroll_admin_route()` | Registers reference admin endpoints `/admin/test_jwt` and `/admin/check/reinstall`. |
| `enroll_graphql_schema_cli()` | Registers `flask generate_schema`, which introspects a live Shopify store and emits an `sgqlc` schema module. |

## Authentication decorators

Use the decorator that matches the Shopify surface you are handling. Successful decorators set `g.store_key` and `g.store_id` for downstream handlers.

| Decorator | Use case |
|---|---|
| `check_callback` | Shopify OAuth callback validation. |
| `check_hmac` | Embedded-app entry validation. |
| `check_proxy` | Shopify app proxy signature validation. |
| `check_webhook` | Shopify webhook HMAC validation through `X-Shopify-Hmac-Sha256`. |
| `check_session_jwt` | Shopify session-token validation from the `Authorization` header. |
| `validate_internal_hash` | Rolling internal hash validation for proxy-style endpoints. |

Deprecated JWT helpers such as `check_jwt`, `validate_jwt`, and `create_admin_jwt_token` remain available for backward compatibility, but new admin endpoints should use `check_session_jwt`.

## Models

The bundled `flask_shopify_utils.model` module provides:

- `Store`: shop domain, access token, scopes, and JSON-style `extra` data storage.
- `Webhook`: webhook job/event records with status helpers.
- `BasicMethod`: small create/update helper methods shared by the models.

Because the model module uses the SQLAlchemy instance registered by `ShopifyUtil`, initialize the extension before importing these models.

## GraphQL utilities

`GraphQLClient` wraps `sgqlc.endpoint.http.HTTPEndpoint`, resolves the Shopify API version through `get_version()`, and retries throttled or temporary HTTP failures.

```python
from flask_shopify_utils.utils import GraphQLClient

client = GraphQLClient("example.myshopify.com", "shpat_access_token")
operation = ...  # Build an sgqlc Operation from your generated schema.
data = client.fetch_data(operation)
```

To generate a typed Shopify schema after registering the CLI command:

```bash
flask generate_schema --store_id 1
```

Use `flask generate_schema --help` to see all available options.

## Development

Clone the repository, create a virtual environment, and install development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
pip install -e .
```

With `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements/dev.txt
uv pip install -e .
```

Run linting and tests:

```bash
flake8
pytest
```

With `uv`:

```bash
uv run flake8
uv run pytest
```

Run a specific test file or test case:

```bash
pytest -vs tests/test_default_routes.py
pytest -vs tests/test_init.py::test_init_app
```

### Dependency locks

Pinned dependencies live in `requirements/`. Use `uv` for new dependency workflows:

```bash
uv pip compile pyproject.toml --extra=dev --output-file=requirements/dev.txt
uv pip compile pyproject.toml --output-file=requirements/index.txt
```

Legacy `pip-tools` commands are still supported:

```bash
pip-compile --extra=dev --output-file=requirements/dev.txt pyproject.toml
pip-compile --output-file=requirements/index.txt pyproject.toml
```

### Build and publish

Build the distribution and verify it with Twine:

```bash
python -m build
twine check dist/*
```

Publish to PyPI when you are ready:

```bash
twine upload dist/* --skip-existing
```

The package version is read from `__version__` in `src/flask_shopify_utils/__init__.py`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Reference

- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
