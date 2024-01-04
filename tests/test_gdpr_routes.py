#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_gdpr_routes.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 12/07/23 11:42 am
"""
from hmac import new as hmac_new
from hashlib import sha256
from json import dumps
from base64 import b64encode


def test_gdpr_routes_enroll(initial_test_client):
    client, test, utils = initial_test_client
    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/webhook/shop/redact', '/webhook/customers/redact', '/webhook/customers/data_request']:
            rules.append(val.rule)
    test.assertEqual(3, len(rules))


def test_redact_routes(initial_test_client):
    client, test, utils = initial_test_client
    for url in ['/webhook/shop/redact', '/webhook/customers/redact', '/webhook/customers/data_request']:
        # Error
        res = client.post(url)
        test.assertEqual(401, res.status_code)
        result = res.get_json()
        test.assertDictEqual(dict(status=401, message='Hmac validation failed!'), result)
        # Success
        data = dumps(dict(a=1, b=2, c='abcde'))
        secret = utils.config.get('SHOPIFY_API_SECRET', 'SHOPIFY_API_SECRET')
        signature = b64encode(hmac_new(secret.encode('utf-8'), data.encode('utf-8'), sha256).digest()).decode('utf-8')
        res = client.post(url, data=data, headers={'X-Shopify-Hmac-Sha256': signature})
        test.assertEqual(200, res.status_code)
        result = res.get_data()
        test.assertEqual(b'success', result)

