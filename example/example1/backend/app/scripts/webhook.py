#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : webhook.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 9/10/23 1:58 pm
"""
from flask import Blueprint, url_for
from click import option
from sgqlc.operation import Operation
from prettytable import PrettyTable
from simplejson import dumps
from functools import wraps
# Custom Modules
# app.schemas.shopify should generate by `flask generate_schema`
from app.schemas.shopify import shopify as shopify_schema
from app.utils.base import BasicHelper

webhook_cli = Blueprint('webhook_cli', __name__, cli_group='webhook')


def check_store_id(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        store_id = kwargs.get('store_id')
        kwargs['helper'] = BasicHelper(store_id, log_name='webhook')
        del kwargs['store_id']
        return func(*args, **kwargs)

    return decorator


@webhook_cli.cli.command('list')
@option('-s', '--store_id', help='Store ID', default=1)
@check_store_id
def webhook_list(helper):
    """ List all registered webhooks """
    table = PrettyTable(field_names=['WebhookID', 'Topic', 'CallbackUrl'])
    cursor = None
    while True:
        op = Operation(shopify_schema.query_type)
        sub = op.webhook_subscriptions(first=20, after=cursor)
        sub.edges.cursor()
        sub.page_info.has_next_page()
        sub.edges.node.id()
        sub.edges.node.endpoint().__as__(shopify_schema.WebhookHttpEndpoint).callback_url()
        sub.edges.node.topic()
        res = helper.gql.fetch_data(op)['webhookSubscriptions']
        for node in res['edges']:
            node = node['node']
            table.add_row([node['id'], node['topic'], node['endpoint']['callbackUrl']])
        if res['pageInfo']['hasNextPage']:
            cursor = res['edges'][-1]['cursor']
        else:
            break
    print('Store: {}'.format(helper.store.key))
    print(table)


@webhook_cli.cli.command('revoke')
@option('-s', '--store_id', help='Store ID', default=1)
@check_store_id
def webhook_revoke(helper):
    """ Revoke registered webhooks """
    table = PrettyTable(field_names=['WebhookID', 'Topic', 'Revoke', 'Message'])
    webhooks = {}
    cursor = None
    while True:
        op = Operation(shopify_schema.query_type)
        query = op.webhook_subscriptions(first=20, after=cursor)
        query.edges.cursor()
        query.edges.node.id()
        query.edges.node.topic()
        query.page_info.has_next_page()
        res = helper.gql.fetch_data(op)['webhookSubscriptions']
        for node in res['edges']:
            node = node['node']
            alias = 'ID{}'.format(node['id'].split('/')[-1])
            webhooks[alias] = dict(id=node['id'], topic=node['topic'])
        if res['pageInfo']['hasNextPage']:
            cursor = res['edges'][-1]['cursor']
        else:
            break
    if len(webhooks.keys()) == 0:
        return print(f'StoreID[{helper.store.id}] does not registered any webhooks')
    op = Operation(shopify_schema.mutation_type, 'RevokeWebhooks')
    for alias in webhooks:
        mutation = op.webhook_subscription_delete(id=webhooks[alias]['id'], __alias__=alias)
        mutation.user_errors()
    res = helper.gql.fetch_data(op)
    for alias in webhooks:
        if alias not in res or len(res[alias]['userErrors']) != 0:
            msg = 'Unknown'
            if alias in res:
                msg = dumps(res[alias]['userErrors'])
            table.add_row([webhooks[alias]['id'], webhooks[alias]['topic'], False, msg])
        else:
            table.add_row([webhooks[alias]['id'], webhooks[alias]['topic'], True, 'Revoked'])
    print('Store: {}'.format(helper.store.key))
    print(table)


@webhook_cli.cli.command('init')
@option('-s', '--store_id', help='Store ID', default=1)
@check_store_id
def webhook_register(helper):
    """ Register webhooks """
    topics = dict()
    common = dict(_scheme='https', _external=True)
    topics['APP_UNINSTALLED'] = url_for('shopify.shop_redact', **common)
    table = PrettyTable(field_names=['Topic', 'CallbackUrl', 'Message'])
    op = Operation(shopify_schema.mutation_type, 'RegisterWebhooks')
    for topic in topics:
        mutation = op.webhook_subscription_create(topic=topic, webhook_subscription=dict(
            callback_url=topics[topic]
        ), __alias__=topic)
        mutation.user_errors()
    res = helper.gql.fetch_data(op)
    for topic in topics:
        if topic not in res or len(res[topic]['userErrors']) != 0:
            msg = 'Unknown'
            if topic in res:
                msg = dumps(res[topic]['userErrors'])
            table.add_row([topic, topics[topic], msg])
        else:
            table.add_row([topic, topics[topic], 'Success'])
    print('Store: {}'.format(helper.store.key))
    print(table)
