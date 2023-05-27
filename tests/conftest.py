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


@fixture
def app():
    app_instance = Flask(__name__)
    return app_instance


@fixture
def shopify_utils(app):
    return ShopifyUtil(app)
