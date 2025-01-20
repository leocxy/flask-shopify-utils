#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_query.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:16
"""
from types import FunctionType
from app.schemas.query import query_webhooks


def test_query_webhooks(test_instance) -> None:
    try:
        query_webhooks()
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
        if isinstance(getattr(query_schema, item), FunctionType):
            fn = 'test_{}'.format(item)
            if fn not in COVERAGE_FUNCS:
                funcs.append(fn)

    if len(funcs) == 0:
        assert True, 'All functions are covered'
    else:
        assert False, 'Not covered functions: {}'.format(' , '.join(funcs))
