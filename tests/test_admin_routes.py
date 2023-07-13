#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : admin_routes.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 12/07/23 2:11 pm
"""


def test_admin_routes_enroll(utils):
    utils.enroll_admin_route()
    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/admin/test_jwt', '/admin/check/<action>']:
            rules.append(val.rule)
    assert 2 == len(rules)


def test_check_jwt_route(utils):
    utils.enroll_admin_route()
    client = utils.app.test_client()
    res = client.get('/admin/test_jwt')
    assert res.status_code == 200
    result = res.get_json()
    assert 500 == result.get('status')
    assert 'Not enough segments' == result.get('message')
    utils.config['BYPASS_VALIDATE'] = 1
    res = client.get('/admin/test_jwt')
    assert res.status_code == 200
    result = res.get_json()
    assert 0 == result.get('status')
    assert 'success' == result.get('message')
