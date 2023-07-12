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


def test_gdpr_routes_enroll(utils):
    utils.enroll_gdpr_route()

    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/webhook/shop/redact', '/webhook/customers/redact', '/webhook/customers/data_request']:
            rules.append(val.rule)
    assert 3 == len(rules)


def test_redact_routes(utils):
    utils.enroll_gdpr_route()
    client = utils.app.test_client()
    for url in ['/webhook/shop/redact', '/webhook/customers/redact', '/webhook/customers/data_request']:
        # Error
        res = client.post(url)
        assert res.status_code == 401
        result = res.get_json()
        assert result.get('status') == 401
        assert result.get('mes'
                          'sage') == 'Hmac validation failed!'
        # Success
        data = dumps(dict(a=1, b=2, c='abcde'))
        secret = utils.config.get('SHOPIFY_API_SECRET', '')
        signature = hmac_new(secret.encode('utf-8'), data.encode('utf-8'), sha256).hexdigest()
        res = client.post(url, data=data, headers={'X-Shopify-Hmac-Sha256': signature})
        assert res.status_code == 200
        result = res.get_data()
        assert str(result, encoding='utf-8') == 'success'
