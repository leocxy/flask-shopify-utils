#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 19/07/23 2:21 pm

App Initialization
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_shopify_utils import ShopifyUtil

__version__ = '0.2.0'
__author__ = 'Leo Chen'
__email__ = 'leo.cxy88@gmail.com'
__copyright__ = 'Copyright 2021, Pocket Square'
# Global Setting
app = None
db = None
utils = None


def create_app(test_config: dict = None):
    global app, db, utils
    app = Flask(__name__)
    # Load Config From Object
    app.config.from_object('app.config.Config')
    # Update Testing Config
    if test_config:
        app.config.update(test_config)

    # Add custom codes here

    # Init Database
    db = SQLAlchemy()
    db.init_app(app)
    Migrate(app, db)

    # Initial Shopify Utils
    utils = ShopifyUtil()
    utils.init_app(app)
    # Initial Shopify Utils Routes
    utils.enroll_default_route()
    utils.enroll_admin_route()
    utils.enroll_gdpr_route()
    utils.enroll_graphql_schema_cli()

    if test_config is not None:
        return app, db
    return app


__all__ = (app, db, utils, create_app)
