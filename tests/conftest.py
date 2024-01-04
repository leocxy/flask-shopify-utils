#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : conftest.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 5:07 pm
"""
from pytest import fixture
from unittest import TestCase
from flask import Flask
from flask_shopify_utils import ShopifyUtil
from flask_sqlalchemy import SQLAlchemy


@fixture(scope='session')
def initial():
    """ Initial the flask app and utils """
    test = TestCase()
    test.maxDiff = None

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy()
    db.init_app(app)

    utils = ShopifyUtil()
    utils.init_app(app)
    # default routes
    utils.enroll_admin_route()
    utils.enroll_default_route()
    utils.enroll_gdpr_route()
    utils.enroll_graphql_schema_cli()

    return app, db, test, utils


@fixture(scope='function')
def initial_test_client(initial):
    """ Initial the database """
    app, db, test, utils = initial
    from flask_shopify_utils.model import Store, Webhook
    with app.app_context():
        db.create_all()
        yield app.test_client(), test, utils
