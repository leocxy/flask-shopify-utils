#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : query.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:00:39
"""
from sgqlc.operation import Operation
# custom modules
from .shopify import shopify as shopify_schema


def query_webhooks(cursor: str = None) -> Operation:
    op = Operation(shopify_schema.query_type, 'QueryWebhooks')
    query = op.webhook_subscriptions(first=20, after=cursor)
    query.page_info.has_next_page()
    query.page_info.end_cursor()
    query.nodes.id()
    query.nodes.callback_url()
    query.nodes.topic()
    return op
