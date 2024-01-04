#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : admin_routes.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 12/07/23 2:11 pm
"""


def test_admin_routes_enroll(initial_test_client):
    client, test, utils = initial_test_client
    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/admin/test_jwt', '/admin/check/<action>']:
            rules.append(val.rule)
    test.assertEqual(2, len(rules))


def test_check_jwt_route(initial_test_client):
    client, test, utils = initial_test_client
    utils.config['BYPASS_VALIDATE'] = 0
    res = client.get('/admin/test_jwt')
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertEqual(500, result.get('status'))
    test.assertEqual('Not enough segments', result.get('message'))
    utils.config['BYPASS_VALIDATE'] = 1
    res = client.get('/admin/test_jwt')
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertEqual(0, result.get('status'))
    test.assertEqual('success', result.get('message'))
