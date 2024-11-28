#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_query.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:16
"""
from app.schemas.query import query_webhooks


def test_query_webhooks(test_instance) -> None:
    try:
        query_webhooks()
    except Exception as e:
        assert False, e
