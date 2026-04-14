#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_admin_exampl.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 20/12/23 12:57 pm
"""


def test_api_test_jwt(test_instance) -> None:
    # client, db, test, app_utils = test_instance
    client, test = test_instance
    rv = client.get('/admin/test_jwt')
    expect = dict(status=0, message='success', data=[])
    test.assertDictEqual(rv.get_json(), expect)


def test_api_check_status(test_instance) -> None:
    client, test = test_instance
    rv = client.get('/admin/check/reinstall')
    # the endpoint will check database record and access_token is valid or not
    # because it is fake, it will redirect to the legacy install URL
    # expect = dict(status=0, message='success', data=None)
    # test.assertDictEqual(rv.get_json(), expect)
    data = rv.get_json()
    test.assertIn('https://localhost/install?shop', data['data']['url'])


