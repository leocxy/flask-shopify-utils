#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_mutation.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:53
"""
from types import FunctionType
from app.schemas.mutation import update_meta, update_multiple_meta, create_discount_code, update_discount_code, \
    delete_discount_code, create_auto_discount, update_auto_discount, delete_auto_discount, create_webhooks, \
    revoke_webhooks, create_payment_customization, delete_payment_customization, update_payment_customization, \
    create_delivery_customization, delete_delivery_customization, update_delivery_customization

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
        data['APP_UNINSTALLED'] = dict(callback_url='http://127.0.0.1:500')
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


def test_create_payment_customization() -> None:
    try:
        create_payment_customization(dict(
            function_id='1234',
            enabled=True,
            title='title',
            metafields=[]
        ))
    except Exception as e:
        assert False, e


def test_update_payment_customization() -> None:
    try:
        update_payment_customization('gid://shopify/PaymentCustomization/1234', dict(
            enabled=False,
            title='title'
        ))
    except Exception as e:
        assert False, e


def test_delete_payment_customization() -> None:
    try:
        delete_payment_customization('gid://shopify/PaymentCustomization/1234')
    except Exception as e:
        assert False, e


def test_create_delivery_customization() -> None:
    try:
        create_delivery_customization(dict(
            function_id='1234',
            enabled=True,
            title='title',
            metafields=[]
        ))
    except Exception as e:
        assert False, e


def test_update_delivery_customization() -> None:
    try:
        update_delivery_customization('gid://shopify/DeliveryCustomization/1234', dict(
            enabled=False,
            title='title'
        ))
    except Exception as e:
        assert False, e


def test_delete_delivery_customization() -> None:
    gid = 'gid://shopify/DeliveryCustomization/1234'
    try:
        delete_delivery_customization(gid)
    except Exception as e:
        assert False, e


###
# Coverage check - make sure all functions are covered
###
COVERAGE_FUNCS = [name for name, obj in locals().items() if
                  isinstance(obj, FunctionType) and name.startswith('test_')]


def test_coverage_check() -> None:
    from app.schemas import mutation as mutation_schema
    funcs = []
    for item in dir(mutation_schema):
        if isinstance(getattr(mutation_schema, item), FunctionType):
            fn = 'test_{}'.format(item)
            if fn not in COVERAGE_FUNCS:
                funcs.append(item)

    if len(funcs) == 0:
        assert True, 'All functions are covered'
    else:
        assert False, 'Not covered functions: {}'.format(', '.join(funcs))
