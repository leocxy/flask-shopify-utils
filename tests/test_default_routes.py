#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_default_routes.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 15/06/23 12:42 pm
"""
from urllib.parse import urlencode
from time import time


def test_default_routes_enroll(utils):
    utils.enroll_default_route()

    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/', '/install', '/callback', '/admin']:
            rules.append(val.rule)
    assert 4 == len(rules)


def test_install_route(utils):
    utils.enroll_default_route()
    client = utils.app.test_client()
    # Success
    params = dict(shop='test.myshopify.com')
    res = client.get(f'/install?{urlencode(params)}')
    assert res.status_code == 302
    assert f'https://{params["shop"]}/admin/oauth/authorize' in res.headers.get('Location', '')
    # Error
    params = dict(shop='www.google.com')
    res = client.get(f'/install?{urlencode(params)}')
    assert res.status_code == 200
    result = res.get_json()
    assert result.get('status') == 400


def test_callback_route(utils):
    utils.enroll_default_route()
    client = utils.app.test_client()
    # Error - Cookie
    res = client.get('/callback')
    assert res.status_code == 200
    result = res.get_json()
    assert result.get('status') == 403
    assert result.get('message') == 'Request origin cannot be verified'
    # Initial Cookie
    params = dict(shop='test.myshopify.com')
    res = client.get(f'/install?{urlencode(params)}')
    assert res.status_code == 302
    state = None
    for cookie in res.headers.get('Set-Cookie').split(';'):
        key, value = cookie.split('=')
        if key == 'state':
            state = value
            client.set_cookie(key, value)
    # Error - timestamp expired
    timestamp = int(time()) - 86400 - 1
    params = dict(
        timestamp=timestamp,
        shop='test.myshopify.com',
        code='one_time_oauth_token',
        state=state,
    )
    res = client.get('/callback?{}'.format(urlencode(params)))
    assert res.status_code == 200
    result = res.get_json()
    assert result.get('status') == 401
    assert result.get('message') == 'The request has expired'
    # Error - Hmac mismatch
    timestamp = int(time())
    params = dict(
        timestamp=timestamp,
        shop='test.myshopify.com',
        code='one_time_oauth_token',
        state=state,
    )
    res = client.get('/callback?{}'.format(urlencode(params)))
    assert res.status_code == 401
    result = res.get_json()
    assert result.get('status') == 401
    assert result.get('message') == 'Hmac validation failed!'
    # Pass validation
    params['hmac'] = utils.validate_hmac(params)
    res = client.get('/callback?{}'.format(urlencode(params)))
    assert res.status_code == 500
    result = res.get_json()
    assert result.get('status') == 500
    assert result.get('message') == 'Something went wrong while doing the OAuth!'


def test_index_route(utils):
    utils.enroll_default_route()
    client = utils.app.test_client()
    # none parameters -> docs page
    res = client.get('/')
    assert res.status_code == 302
    assert res.headers.get('Location', '') == '/docs'
    params = dict(
        timestamp=int(time()),
        host='host_token_for_app_bridge',
        shop='test.myshopify.com',
        session='shopify_session_token',
        hmac='test'
    )
    res = client.get('/?{}'.format(urlencode(params)))
    assert res.status_code == 302
    assert '/admin?' in res.headers.get('Location', '')


def test_admin_index_route(utils):
    utils.enroll_default_route()
    client = utils.app.test_client()
    # none parameters -> docs page
    res = client.get('/admin')
    assert res.status_code == 302
    assert res.headers.get('Location', '') == '/docs'
    # Error - Invalid Timestamp
    timestamp = int(time()) - 86400 - 1
    params = dict(
        timestamp=timestamp,
        host='host_token_for_app_bridge',
        shop='test.myshopify.com',
        session='shopify_session_token',
        hmac='test'
    )
    res = client.get('/admin?{}'.format(urlencode(params)))
    assert res.status_code == 401
    result = res.get_json()
    assert result.get('status') == 401
    assert result.get('message') == "The request has expired"
    # Error - Invalid Hmac
    params['timestamp'] = int(time())
    res = client.get('/admin?{}'.format(urlencode(params)))
    assert res.status_code == 401
    result = res.get_json()
    assert result.get('status') == 401
    assert result.get('message') == "Invalid HMAC"
    # Error - No Database Record
    del params['hmac']
    params['hmac'] = utils.validate_hmac(params)
    res = client.get('/admin?{}'.format(urlencode(params)))
    result = res.get_json()
    assert result.get('status') == 404
    assert 'not found in database!' in result.get('message')
    # Bypass - pass
    utils.config['BYPASS_VALIDATE'] = 1
    res = client.get('/admin?{}'.format(urlencode(params)))
    assert res.status_code == 200
    result = res.get_json()
    assert 0 == result.get('status')
    assert 'Oops... The `index.html` is gone!' == result.get('message')
