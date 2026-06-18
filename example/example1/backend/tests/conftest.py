#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : conftest.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 20/12/23 2:15 pm
"""
from os import getenv
from sys import path as sys_path
from pathlib import Path
from pytest import fixture, skip
from unittest import TestCase

# reset the system path
sys_path.append(str(Path(__file__).resolve().parents[1]))
from app import create_app

SNAPSHOT_DIR = Path(__file__).resolve().parent / 'snapshots'


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
            # create table the necessary table only
            metadata = db.MetaData()
            metadata.create_all(bind=db.engine, tables=[Store.__table__])
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


@fixture(scope='function')
def assert_gql():
    """
    Render a sgqlc Operation to GraphQL and compare it against a golden snapshot.
    Generate / update them with:  UPDATE_SNAPSHOTS=1 pytest
    """

    def _assert(name: str, op):
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        path = SNAPSHOT_DIR / '{}.graphql'.format(name)
        actual = str(op).strip() + '\n'

        if getenv('UPDATE_SNAPSHOTS') == '1':
            path.write_text(actual, encoding='utf-8', newline='\n')
            skip('snapshot written: {}'.format(path.name))

        assert path.exists(), \
            'Missing snapshot {}. Run `UPDATE_SNAPSHOTS=1 pytest` to generate it.'.format(path.name)
        expected = path.read_text(encoding='utf-8')
        assert actual == expected, (
            '\nGraphQL output for "{}" does not match the snapshot.\n'
            'If the change is intended, run `UPDATE_SNAPSHOTS=1 pytest` to update it.\n'
            '--- expected ---\n{}\n--- actual ---\n{}'.format(name, expected, actual)
        )

    return _assert


@fixture(scope='function')
def klaviyo(initial):
    """  initial the klaviyo class """
    app, db, app_utils, test = initial
    from app.utils.klaviyo import KlaviyoHelper
    helper = KlaviyoHelper()
    yield helper, test

# custom fixtures
