#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_hmac_calculate.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 5:01 pm
"""
from urllib.parse import urlencode
from flask import request, jsonify


def test_request(app, shopify_utils):
    @app.route('/')
    @shopify_utils.check_hmac
    def test_params():
        return jsonify(dict(status=0, message='success'))

    tc = app.test_client()
    params = dict(test='Yes', val=1234)

    rv = tc.get(f'/?{urlencode(params)}')
    result = rv.get_json()
    assert result.get('status') == 401

    hmac_string = shopify_utils.hmac_calculate(params)
    rv = tc.get(f'/?{urlencode(params)}&hmac={hmac_string}')
    result = rv.get_json()
    assert rv.status_code == 200
    assert result.get('status') == 0


def test_request_with_array(app, shopify_utils):
    @app.route('/')
    @shopify_utils.check_hmac
    def test_params_with_array():
        return jsonify(dict(status=0, message='success'))

    tc = app.test_client()
    params = {
        'test': 'Yes',
        'val': 1234,
        'val2[]': ['Hello', 'world']
    }
    hmac_string = shopify_utils.hmac_calculate(params)
    rv = tc.get(f'/?{urlencode(params)}&hmac={hmac_string}')
    result = rv.get_json()
    assert rv.status_code == 200
    assert result.get('status') == 0
