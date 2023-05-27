#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 26/05/23 1:43 pm
"""
from typing import Optional, Callable
from os import getcwd, path
from time import sleep, time
from urllib.error import HTTPError, URLError
from hashlib import sha256
import hmac
# Third-party Library
from flask import current_app, request, url_for, Blueprint, g, jsonify, Flask
from sgqlc.endpoint.http import HTTPEndpoint
from sgqlc.operation import Operation
from flask_shopify_utils.utils import get_version

__version__ = '0.0.1'


class ShopifyUtil:
    """ Shopify Utils """

    def __init__(self, app: Optional[Flask] = None, config: dict = None) -> None:
        if not (config is None or isinstance(config, dict)):
            raise ValueError("`config` must be an instance of dict or None")
        self._config = config
        if app is not None:
            self.init_app(app, config)

    @property
    def config(self):
        return self._config

    def init_app(self, app: Flask, config: dict = None) -> None:
        """ This is used to initialize your app object """
        if not (config is None or isinstance(config, dict)):
            raise ValueError("`config` must be an instance of dict or None")
        base_config = app.config.copy()
        if self.config:
            base_config.update(self.config)
        if config:
            base_config.update(config)
        config = base_config

        config.setdefault('ROOT_PATH', getcwd())
        config.setdefault('TEMPORARY_PATH', path.join(config.get('ROOT_PATH'), 'tmp'))
        config.setdefault('API_VERSION', get_version())
        config.setdefault('RESTFUL_VERSION', get_version(restful=True))
        config.setdefault('TIMEZONE', 'Pacific/Auckland')
        config.setdefault('SHOPIFY_API_SECRET', 'CUSTOM_APP_SECRET')
        config.setdefault('SHOPIFY_API_KEY', 'CUSTOM_APP_KEY')
        config.setdefault('BYPASS_VALIDATE', False)
        config.setdefault('DEBUG', False)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions.setdefault('shopify_utils', self)
        self._config = config

    def hmac_calculate(self, params: dict):
        def calculate(params):
            def encode_pairs(params):
                for k, v in params.items():
                    if k == 'hmac':
                        continue
                    k = str(k).replace('%', '%25').replace('=', '%3D')
                    v = str(v).replace('%', '%25')
                    yield '{}={}'.format(k, v).replace('&', '%26')

            return '&'.join(sorted(encode_pairs(params)))

        secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'
        return hmac.new(secret.encode(), calculate(params).encode(), sha256).hexdigest()

    def check_hmac(self, func):
        """ Open the embedded app need to verify the Hmac """

        def decorator(*args, **kwargs):
            if not hmac.compare_digest(
                    self.hmac_calculate(request.args),
                    request.args.get('hmac', '')
            ):
                resp = jsonify(dict(message='Invalid HMAC', status=401))
                resp.status_code = 401
                return resp
            # Get `shop` from request.args
            return func(*args, **kwargs)

        return decorator

    def check_callback(self, func):
        def decorator(*args, **kwargs):
            # check cookie
            state = request.cookies.get('state')
            if state is None or state != request.args.get('state'):
                return jsonify(dict(message='Request origin cannot be verified'), status=403)
            # check time
            if int(request.args.get('timestamp', 0)) < (time() - 86400):
                return jsonify(dict(message='The request has expired', status=401))
            if not hmac.compare_digest(
                    self.hmac_calculate(request.args),
                    request.args.get('hmac', '')
            ):
                resp = jsonify(dict(message='Hmac validation failed!', status=401))
                resp.status_code = 401
                return resp
            return func(*args, *kwargs)

        return decorator

    def check_proxy(self, func):
        def decorator(*args, **kwargs):
            signature = request.args.get('signature', '')
            params = dict((key, value) for key, value in request.args.items() if key != 'signature')
            query = ''
            for key in sorted(params):
                query += '{}={}'.format(key, params[key].join(',') if isinstance(params[key], list) else params[key])
            secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'

            if not hmac.compare_digest(
                    signature,
                    hmac.new(secret.encode('utf-8'), query.encode('utf-8'), sha256).hexdigest()
            ):
                resp = jsonify(dict(
                    message='Proxy validation failed!',
                    headers=dict(request.headers),
                    params=request.args,
                    status=401,
                ))
                resp.status_code = 401
                return resp
            return func(*args, **kwargs)

        return decorator

    def check_webhook(self, func):
        def decorator(*args, **kwargs):
            signature = request.headers.get('X-Shopify-Hmac-Sha256', None)
            if not signature:
                return jsonify(dict(message='Invalid Hmac Header, Please refresh the page'), status=401)
            data = request.get_data()
            secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'
            if not hmac.compare_digest(
                    signature,
                    hmac.new(secret.encode('utf-8'), data, sha256).hexdigest()
            ):
                resp = jsonify(dict(message='Hmac validation failed!', status=401))
                resp.status_code = 401
                return resp
            return func(*args, **kwargs)

        return decorator

    # Admin URL
    # Shopify Default URL
    # Docs URL
    # Customer Data Webhook


class GraphQLClient:
    def __init__(self, app_url: str, token: str, timeout: int = 15):
        self.version = get_version()
        self.timeout = timeout
        self.url = f'https://{app_url}/admin/api/{self.version}/graphql.json'
        self.headers = {'X-Shopify-Access-Token': token}
        self._client = HTTPEndpoint(self.url, self.headers, timeout)

    @property
    def client(self):
        return self._client

    def fetch_data(self, query: Operation, timeout: int = None, attempts: int = 5):
        try:
            result = self.client(query, timeout=timeout if timeout else self.timeout)
            if 'errors' in result.keys():
                if result['errors'][0]['message'] == 'Throttled':
                    if attempts <= 0:
                        raise Exception(result)
                    sleep(2)
                    attempts -= 1
                    return self.fetch_data(query, timeout, attempts)
                raise Exception(result)
        except (HTTPError, URLError) as e:
            if attempts <= 0:
                raise e
            sleep(1)
            attempts -= 1
            return self.fetch_data(query, timeout, attempts)
