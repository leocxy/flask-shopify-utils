### Introduction

This is the backend of the Shopify App. It is a Flask web application.
I am using `flask-shopify-utils` to simplify the Shopify App development.
The package keep all core functions and manager the core dependencies version. 
I will update it every quarter to keep Shopify API up to date.

For any extra dependencies, please add them to `pyproject.toml` and run `pip-compile` to generate the dependencies file.

### Environment

- OS: MacOX / Centos
- Python: ^3.8

---

### Configuration

You should use Shopify CLI to pull the app configs from the root folder.

### Local Development

```shell

# Access the project
>cd /path/to/project/backend

# Create virtual env
>virtualenv .venv

# Active virtual env
>source .venv/bin/active

# Install dependencies
>pip install -r requirements/index.txt

# Run flask 
>flask run
```

### Generate dependencies file

All python dependencies are managed by pip-tools. You can use the following command to generate the dependencies file.

```shell

# Install pip-tools
>pip install pip-tools

# Generate dependencies file
>pip-compile -o requirements/index.txt pyproject.toml

# Generate development dependencies file
>pip-compile --extra=dev -o requirements/dev.txt pyproject.toml

```

### Unit Test

```shell
# Install the necessary dependencies for testing
>pip install -r requirements/dev.txt

# Run all unit test
>pytest

# Run a specific unit test
>pytest -s -v tests/test_app.py
```