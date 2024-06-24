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


def test_default_routes_enroll(initial_test_client):
    client, test, utils = initial_test_client
    rules = []
    for val in utils.app.url_map.iter_rules():
        if val.rule in ['/', '/install', '/callback', '/admin']:
            rules.append(val.rule)
    test.assertEqual(4, len(rules))


def test_install_route(initial_test_client):
    client, test, utils = initial_test_client
    # Success
    params = dict(shop='test.myshopify.com')
    res = client.get(f'/install?{urlencode(params)}')
    test.assertEqual(res.status_code, 302)
    test.assertIn(f'https://{params["shop"]}/admin/oauth/authorize', res.headers.get('Location', ''))
    # Error
    params = dict(shop='www.google.com')
    res = client.get(f'/install?{urlencode(params)}')
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertEqual(result.get('status'), 400)


def test_callback_route(initial_test_client):
    client, test, utils = initial_test_client
    # Error - Cookie
    res = client.get('/callback')
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=403, message='Request origin cannot be verified'))
    # Initial Cookie
    params = dict(shop='test.myshopify.com')
    res = client.get(f'/install?{urlencode(params)}')
    test.assertEqual(res.status_code, 302)
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
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=401, message='The request has expired'))
    # Error - Hmac mismatch
    timestamp = int(time())
    params = dict(
        timestamp=timestamp,
        shop='test.myshopify.com',
        code='one_time_oauth_token',
        state=state,
    )
    res = client.get('/callback?{}'.format(urlencode(params)))
    test.assertEqual(res.status_code, 401)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=401, message='Hmac validation failed!'))
    # Pass validation
    params['hmac'] = utils.validate_hmac(params)
    res = client.get('/callback?{}'.format(urlencode(params)))
    test.assertEqual(res.status_code, 500)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=500, message='Something went wrong while doing the OAuth!', data=[]))


def test_index_route(initial_test_client):
    client, test, utils = initial_test_client
    # none parameters -> docs page
    res = client.get('/')
    test.assertEqual(res.status_code, 302)
    test.assertEqual(res.headers.get('Location', ''), '/docs')
    params = dict(
        timestamp=int(time()),
        host='host_token_for_app_bridge',
        shop='test.myshopify.com',
        session='shopify_session_token',
        hmac='test'
    )
    res = client.get('/?{}'.format(urlencode(params)))
    test.assertEqual(res.status_code, 302)
    test.assertIn('/admin?', res.headers.get('Location', ''))


def test_admin_index_route(initial_test_client):
    client, test, utils = initial_test_client
    # none parameters -> docs page
    res = client.get('/admin')
    test.assertEqual(res.status_code, 302)
    test.assertEqual(res.headers.get('Location', ''), '/docs')
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
    test.assertEqual(res.status_code, 401)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=401, message='The request has expired', data=[]))
    # Error - Invalid Hmac
    params['timestamp'] = int(time())
    res = client.get('/admin?{}'.format(urlencode(params)))
    test.assertEqual(res.status_code, 401)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=401, message='Invalid HMAC', data=[]))
    # Bypass - pass
    params['hmac'] = utils.validate_hmac(params)
    utils.config['BYPASS_VALIDATE'] = 1
    res = client.get('/admin?{}'.format(urlencode(params)))
    test.assertEqual(res.status_code, 200)
    result = res.get_json()
    test.assertDictEqual(result, dict(status=0, message='Oops... The `index.html` is gone!', data=[]))
