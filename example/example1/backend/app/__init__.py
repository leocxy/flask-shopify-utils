#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 11/09/23 9:25 am
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import getenv
from logging.config import dictConfig
from flask_shopify_utils import ShopifyUtil

__version__ = '0.2.0'
__author__ = 'Leo Chen'
__email__ = 'leo.cxy88@gmail.com'
__copyright__ = 'Copyright © PocketSquare'
# Global Setting
app = Flask(__name__)
db = SQLAlchemy()
app_utils = ShopifyUtil()


def create_app(test_config: dict = None):
    # Load Config From Object
    app.config.from_object('app.config.Config')

    # init azure monitor after loading config from .env
    azure_monitor = getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    if azure_monitor:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        configure_azure_monitor(
            connection_string=azure_monitor,
            resource_attributes={"service.name": "shopify-custom-app-backend"},
            instrumentation_options={
                "flask": {"enabled": False},
                "azure_sdk": {"enabled": False}
            },
        )
        FlaskInstrumentor().instrument_app(app)
    else:
        dictConfig({
            'version': 1,
            "disable_existing_loggers": False,
            'root': {
                'level': 'DEBUG' if getenv('FLASK_DEBUG', '0') == '1' else 'INFO',
            }
        })

    # Update Testing Config
    if test_config:
        app.config.update(test_config)

    # Init Database
    db.init_app(app)
    Migrate(app, db)

    # Initial Shopify Utils
    app_utils.init_app(app)
    # Initial Shopify routes
    app_utils.enroll_default_route()
    app_utils.enroll_admin_route()
    app_utils.enroll_gdpr_route()
    app_utils.enroll_graphql_schema_cli()

    # Init Routes
    from .routes import register_routes
    register_routes(app)

    # Init Script
    from .scripts import register_scripts
    register_scripts(app)

    if test_config is not None:
        return app, db, app_utils
    return app


__all__ = (app, db, app_utils, create_app)
