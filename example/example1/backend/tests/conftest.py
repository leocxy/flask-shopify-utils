#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : conftest.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 20/12/23 2:15 pm
"""
import sys
from pytest import fixture
from unittest import TestCase
from os.path import abspath, dirname

# reset the system path
sys.path.append(abspath(dirname(dirname(__file__))))
from app import create_app


@fixture(scope='session')
def initial():
    """ Initial the flask app and configs """
    test = TestCase()
    test.maxDiff = None

    app, db, app_utils = create_app({
        'TESTING': True,
        'FLASK_DEBUG': 1,
        'BYPASS_VALIDATE': 1,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SCOPES': 'write_customers,write_orders,read_products',
    })

    return app, db, app_utils, test


@fixture(scope='function')
def test_instance(initial):
    """  initial the database """
    app, db, app_utils, test = initial
    from flask_shopify_utils.model import Store
    with app.test_client() as client:
        with app.app_context():
            # create table
            db.create_all()
            record = Store(
                key='test.myshopify.com',
                domain='teststore.com',
                scopes='write_customers,write_orders,read_products',
                # You need to grab this from DB if you need to query product
                token='test_token'
            )
            db.session.add(record)
            db.session.commit()
            app.config['BYPASS_VALIDATE'] = record.id
            yield client, test
