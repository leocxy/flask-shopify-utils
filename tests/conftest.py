#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : conftest.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 5:07 pm
"""
from pytest import fixture
from flask import Flask
from flask_shopify_utils import ShopifyUtil
from flask_sqlalchemy import SQLAlchemy


@fixture
def utils():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy()
    db.init_app(app)
    utils = ShopifyUtil(app)
    with app.app_context():
        from flask_shopify_utils.model import Store, Webhook
        db.create_all()
        yield utils
