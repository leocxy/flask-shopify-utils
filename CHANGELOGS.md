# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.14] - 2026-06-26

Changes relative to `0.2.13`.

### Changed

- `GraphQLClient.fetch_data` now accepts an optional `headers` dict, forwarded to the underlying endpoint as `extra_headers`, so callers can attach per-request headers. Also added a `HTTPEndpoint` return-type annotation to the `client` property (`7191697`).

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
