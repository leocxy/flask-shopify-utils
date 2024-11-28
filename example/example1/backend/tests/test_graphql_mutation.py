#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_mutation.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:53
"""
from app.schemas.mutation import update_meta, update_multiple_meta, create_discount_code, update_discount_code, \
    delete_discount_code, create_auto_discount, update_auto_discount, delete_auto_discount, create_webhooks, \
    revoke_webhooks

DISCOUNT_CODE_DATA = dict(
    code='test_code',
    combines_with=dict(
        product_discount=True,
        order_discount=True,
        shipping_discount=True
    ),
    applies_once_per_customer=True,
    title='test_title',
    usage_limit=10,
    starts_at='2000-01-01T00:00:00',
)

AUTO_DISCOUNT_DATA = dict(
    applies_on_subscription=False,
    combines_with=dict(
        product_discount=True,
        order_discount=True,
        shipping_discount=True
    ),
    starts_at='2000-01-01T00:00:00',
    function_id='FUNCTION_ID',
    metafields=[dict(
        namespace='namespace',
        key='key',
        type='single_line_text',
        value='test_value'
    )],
    title='test_title',
)


def test_update_meta():
    try:
        update_meta(
            'gid://shopify/Customer/123456',
            'test_value',
            'namespace',
            'key',
            'single_line_text'
        )
    except Exception as e:
        assert False, e


def test_update_multiple_meta():
    try:
        update_multiple_meta([
            dict(
                owner_id='gid://shopify/Customer/123456',
                namespace='namespace',
                key='key',
                type='single_line_text',
                value='test_value'
            )
        ])
    except Exception as e:
        assert False, e


def test_create_discount_code():
    try:
        create_discount_code(DISCOUNT_CODE_DATA)
    except Exception as e:
        assert False, e


def test_update_discount_code():
    try:
        update_discount_code('gid://shopify/DiscountCodeNode/123456', DISCOUNT_CODE_DATA)
    except Exception as e:
        assert False, e


def test_delete_discount_code():
    try:
        delete_discount_code('123456')
    except Exception as e:
        assert False, e


def test_create_auto_discount():
    try:
        create_auto_discount(AUTO_DISCOUNT_DATA)
    except Exception as e:
        assert False, e


def test_update_auto_discount():
    try:
        update_auto_discount('gid://shopify/DiscountCodeNode/123456', AUTO_DISCOUNT_DATA)
    except Exception as e:
        assert False, e


def test_delete_auto_discount():
    try:
        delete_auto_discount('123456')
    except Exception as e:
        assert False, e


def test_create_webhooks():
    try:
        data = dict()
        data['APP_UNINSTALLED'] = 'http://127.0.0.1:500'
        create_webhooks(data)
    except Exception as e:
        assert False, e


def test_revoke_webhooks():
    try:
        data = dict()
        data['ALIAS_ID'] = dict(id='owner_id', topic='topic')
        revoke_webhooks(data)
    except Exception as e:
        assert False, e
