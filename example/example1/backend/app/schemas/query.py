#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : query.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:00:39
"""
from sgqlc.operation import Operation
from typing import TypedDict
from typing_extensions import NotRequired
# custom modules
from .shopify import shopify as shopify_schema


class QueryMeta(TypedDict):
    namespace: str
    key: str
    alias: str
    is_json: NotRequired[bool]


def format_meta_list(query, meta_list: list[QueryMeta] = None) -> None:
    if not meta_list:
        return
        # meta data
    for val in meta_list:
        v = query.metafield(namespace=val['namespace'], key=val['key'], __alias__=val['alias'])
        is_json = val.get('is_json')
        v.value() if is_json is None or not is_json else v.json_value()


def query_webhooks(cursor: str = None) -> Operation:
    op = Operation(shopify_schema.query_type, 'QueryWebhooks')
    query = op.webhook_subscriptions(first=20, after=cursor)
    query.page_info.has_next_page()
    query.page_info.end_cursor()
    query.nodes.id()
    query.nodes.callback_url()
    query.nodes.topic()
    return op


def query_delivery_customization(gid: str, namespace: str, key: str) -> Operation:
    op = Operation(shopify_schema.query_type, 'QueryDeliveryCustomization')
    query = op.delivery_customization(id=gid)
    query.title()
    query.enabled()
    query.metafield(namespace=namespace, key=key).json_value()
    return op


def query_payment_customization(gid: str, namespace: str, key: str) -> Operation:
    op = Operation(shopify_schema.query_type, 'QueryPaymentCustomization')
    query = op.payment_customization(id=gid)
    query.title()
    query.enabled()
    query.metafield(namespace=namespace, key=key).json_value()
    return op
