# Flask-Shopify-Utils

The utils for Flask Application that build for Shopify Custom App 

---

# Installing

```shell
$pip install -U flask-shopify-utils
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

- Upgrade `pip` and `setuptools`

```shell
$ python -m pip install --upgrade pip setuptools
```

- Install the development dependencies, then install `Flask-ShopifyUtils` in editable mode.

```sheel
$ pip install -r requirements/dev.txt && pip install -e .
```

## Running the tests

Make sure you have install the repository locally.

```shell
$ pip install -e .
$ pytest
```

