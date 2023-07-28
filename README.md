# Flask-Shopify-Utils

The utils for Flask Application that build for Shopify Custom App 

---

# Installing

```shell
$pip install -U flask-shopify-utils
```

---

## Example / How to ...

Please check the `example` folder for more details.

Remember, this package is using Flask-SQLAlchemy, so you need to initialize the database first.

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_shopify_utils import ShopifyUtil

app = Flask(__name__)
# Init Database
db = SQLAlchemy()
db.init_app(app)

# Initial Shopify Utils
utils = ShopifyUtil()
utils.init_app(app)

# example: register default routes
utils.enroll_default_route()

```

---

## Donate

Well, I have no idea how this work, just copy it from somewhere.

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today](https://palletsprojects.com/donate)

---

## First time setup

- Download the repository to your local machine.
- Create a virtualenv.

```shell
# Linux/macOS
$ python3 -m venv env
$ . env/bin/active

# Window
$ py -3 -m venv env
$ env/Scripts/active
```

- Install `pip-tools`, `twine` and `build` in the virtualenv. 

```shell
>pip install --upgrade pip
>pip install pip-tools twine build
```

- Install the development dependencies, then install `Flask-ShopifyUtils` in editable mode.

```sheel
$ pip install -r requirements/dev.txt && pip install -e .
```

- Build the wheel
```shell
# new 
>python -m build
# For more reference https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
```

- Deploy to PyPI

```shell
# check
>twine check dist/*
# upload
>twine upload dist/*
```

## requirements.txt

All dependencies are managed by `pip-tools`, so you need to install it first.
And you can find them from the `requirements` folder.

```shell
# development
>pip-compile --extra=dev --output-file=requirements/dev.txt pyproject.toml

# production
>pip-compile --output-file=requirements/index.txt pyproject.toml
````

## Running the tests

Make sure you have install the repository locally.

```shell
# install the package
>pip install -e .
# install the pytest
>pip install pytest
# run all tests
>pytest
# run tests with output
>pytest -s
# run specific test
>pytest -v tests/test_init.py
```

---

# Reference
[Packing for Python](https://packaging.python.org/en/latest/tutorials/installing-packages/)