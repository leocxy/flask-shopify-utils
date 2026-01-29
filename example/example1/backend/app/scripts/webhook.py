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
from prettytable import PrettyTable
from simplejson import dumps
from functools import wraps
# Custom Modules
# app.schemas.shopify should generate by `flask generate_schema`
from app.utils.base import BasicHelper
from app.schemas.query import query_webhooks
from app.schemas.mutation import revoke_webhooks, create_webhooks

webhook_cli = Blueprint('webhook_cli', __name__, cli_group='webhook')
webhook_cli.cli.short_help = 'Webhook CLIs'


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
        op = query_webhooks(cursor)
        res = helper.gql.fetch_data(op)['webhookSubscriptions']
        for node in res['nodes']:
            table.add_row([node['id'], node['topic'], node['callbackUrl']])
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
        op = query_webhooks(cursor)
        res = helper.gql.fetch_data(op)['webhookSubscriptions']
        for node in res['nodes']:
            alias = 'ID{}'.format(node['id'].split('/')[-1])
            webhooks[alias] = dict(id=node['id'], topic=node['topic'])
        if res['pageInfo']['hasNextPage']:
            cursor = res['edges'][-1]['cursor']
        else:
            break
    if len(webhooks.keys()) == 0:
        return print(f'StoreID[{helper.store.id}] does not registered any webhooks')

    # revoke webhook
    op = revoke_webhooks(webhooks)
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
    topics['APP_UNINSTALLED'] = dict(
        uri=url_for('shopify_gdpr.shop_redact', **common),
    )
    table = PrettyTable(field_names=['Topic', 'CallbackUrl', 'Message'])

    op = create_webhooks(topics)
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
