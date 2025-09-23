#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_query.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:16
"""
from types import FunctionType
from app.schemas.query import query_webhooks, query_delivery_customization, query_payment_customization, \
    query_shopify_functions


def test_query_webhooks(test_instance) -> None:
    try:
        query_webhooks()
    except Exception as e:
        assert False, e


def test_query_delivery_customization() -> None:
    try:
        query_delivery_customization('gid://shopify/DeliveryCustomization/123456', 'namespace', 'key')
    except Exception as e:
        assert False, e


def test_query_payment_customization() -> None:
    try:
        query_payment_customization('gid://shopify/PaymentCustomization/123456', 'namespace', 'key')
    except Exception as e:
        assert False, e


def test_query_shopify_functions() -> None:
    try:
        query_shopify_functions()
        query_shopify_functions(10)
        query_shopify_functions(10, 'cursor')
    except Exception as e:
        assert False, e


###
# Coverage check - make sure all functions are covered
###
COVERAGE_FUNCS = [name for name, obj in locals().items() if isinstance(obj, FunctionType) and name.startswith('test_')]


def test_coverage_check() -> None:
    from app.schemas import query as query_schema
    funcs = []
    for item in dir(query_schema):
        # exclude methods
        if item in ['TypedDict', 'format_meta_list']:
            continue
        if isinstance(getattr(query_schema, item), FunctionType):
            fn = 'test_{}'.format(item)
            if fn not in COVERAGE_FUNCS:
                funcs.append(item)

    if len(funcs) == 0:
        assert True, 'All functions are covered'
    else:
        assert False, 'Not covered functions: {}'.format(', '.join(funcs))
