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
$ pip install -r requirements.txt && pip install -e .
```

- Build the wheel
```shell
>pip install wheel setuptools twine build
# deprecated
>python setup.py bdist_wheel
# new 
>python -m build
# For more reference https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
```

## Generate the requirements.txt

Once you customize the `steup.cfg`, you should update the `requirements.txt`. 

```shell
>pip-compile --output-file=requirements.txt
````

## Running the tests

Make sure you have install the repository locally.

```shell
# install the package
$ pip install -e .
# install the pytest
& pip install pytest
# run all tests
$ pytest
# run tests with output
$ pytest -s
# run specific test
$ pytest -v tests/test_init.py
```

