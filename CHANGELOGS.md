# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.2] - 2026-07-15

Changes relative to `0.3.1`.

### Added

- `flask token migrate` — a one-off CLI (under the new `token` command group) that migrates a store's non-expiring (offline) access token to an expiring token via Shopify's OAuth token-exchange grant (`grant_type=urn:ietf:params:oauth:grant-type:token-exchange`). It takes `-s/--store_id`, runs under `prevent_concurrency`, and refuses to run when the store is missing, soft-deleted, or already holding a `refresh_token`; a `401` response soft-deletes the store (sets `deleted_at`).

### Changed

- **Breaking:** the expiring-token CLIs were regrouped under a new `token` Click group. `flask refresh_expiring_token` (added in `0.3.1`) is now `flask token refresh`; `flask generate_schema` is unchanged. Internally `enroll_graphql_schema_cli`'s single `cli_bp` blueprint was split into `graphql_cli` (schema) and `access_token_cli` (token).
- `flask token refresh` now runs inside `prevent_concurrency` (key `refresh_expiring_token`) so overlapping runs can't refresh the same stores concurrently.
- The OAuth `callback` now clears the expiring-token bookkeeping columns (`token_expired_at`, `refresh_token`, `refresh_expired_at` reset to `None`) when a non-expiring token is issued and the response carries no `refresh_token`, so a store downgraded from expiring back to offline tokens no longer keeps stale expiry data.

## [0.3.1] - 2026-07-07

Changes relative to `0.2.14`.

### Added

- Expiring (online) access-token support in the OAuth flow, gated by the new `EXPIRING_TOKEN` config. When set to `1`, `enroll_default_route`'s install handler appends `expiring=1` to the callback `redirect_uri`, and `callback` requests an expiring token; on success it persists `refresh_token`, `token_expired_at` (now + 3600s) and `refresh_expired_at` (now + 90 days).
- `Store` model gains four columns: `token_expired_at`, `refresh_token`, `refresh_expired_at` (expiring-token bookkeeping) and `deleted_at` (soft-delete marker).
- `enroll_graphql_schema_cli` registers a new `flask refresh_expiring_token` command that pages through every store holding a `refresh_token`, refreshes any online token within 30 minutes of expiry via the `refresh_token` grant, and soft-deletes (sets `deleted_at`) any store whose refresh returns `401` (app uninstalled).
- Example scaffold migration `3d1b6925999f` adds the four new `stores` columns.
- The example scaffold's `app/schemas/default_mutation.py` gains a `_inject_directive` helper that splices a GraphQL `@idempotent(key: …)` directive into an sgqlc-rendered mutation string (sgqlc has no native directive support), with optional `alias` support for targeting aliased fields.

### Changed

- **Breaking:** `GraphQLClient.fetch_data` no longer raises on error responses. It now returns `Tuple[bool, Union[str, dict]]` — `(True, data)` on success, `(False, error)` on a throttle exhaustion, GraphQL error, `401`, or `HTTPError`/`URLError`. This resolves the long-standing "make `fetch_data` non-raising" TODO. The `headers` argument added in `0.2.14` was also removed.
- The example scaffold (`app/utils/__init__.py`, `app/scripts/webhook.py`) is updated to the new tuple contract: every `fetch_data` call now unpacks `rs, res = ...` and handles the `not rs` failure branch with a warning log and an early return.
- Store lookups in the OAuth callback, the embedded-app entry points (`/`, `/admin`), and the schema CLI now filter on `deleted_at IS NULL`, so soft-deleted stores are treated as uninstalled.
- Dependencies: added `python-dateutil < 3` (used for the `relativedelta` token-expiry math); relaxed the pinned `click == 8.1.8` to `click < 9` and the dev-only `build == 1.2.1` to `build < 2`.
- `enroll_graphql_schema_cli` now serialises the introspected schema with `simplejson.dump` instead of the stdlib `json.dump`.

### Removed

- **Breaking:** Dropped Python 3.9 support; the minimum supported version is now 3.10 (`requires-python >= 3.10`, the CI matrix, the package classifiers, and the README badge are all updated).

## [0.2.14] - 2026-06-26

Changes relative to `0.2.13`.

### Changed

- `GraphQLClient.fetch_data` now accepts an optional `headers` dict, forwarded to the underlying endpoint as `extra_headers`, so callers can attach per-request headers. Also added a `HTTPEndpoint` return-type annotation to the `client` property.

## [0.2.13] - 2026-06-18

Changes relative to `0.2.12`.

### Added

- `model.BasicMethod` now declares a `query: ClassVar[Query]` annotation, improving type hints on derived models (`08e8f36`).
- The example scaffold (`example/example1`) gains mutation/query snapshot tests covering the default discount, delivery/payment customization, webhook, and metafield operations (`4c12b46`).

### Changed

- `lazy-dog` directory copying is now merge-based: same-named files are overwritten while destination-only files are preserved; the old "overwrite the whole directory" prompt is reworded to "overwrite files with the same names" (`08e8f36`).
- Updated the example scaffold's Shopify GraphQL schema and renamed `schemas/mutation.py` and `schemas/query.py` to `default_mutation.py` and `default_query.py` (`905b318`).
- Expanded the README with global install instructions for `lazy-dog` (`pip install --user` / `uv tool install`), a command option table, and tidied configuration and route tables.

### Fixed

- Fixed `lazy-dog` failing to locate the scaffold when downloading from a non-`master` branch: instead of assuming the extracted directory carries a `-master` suffix, it now scans the extraction root dynamically for `example/example1` (`08e8f36`).
