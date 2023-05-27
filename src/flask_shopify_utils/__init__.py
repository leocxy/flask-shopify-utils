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
from datetime import datetime
# Third-party Library
from flask import current_app, request, url_for, Blueprint, g, Flask
from sgqlc.endpoint.http import HTTPEndpoint
import shopify

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
        config.setdefault('API_VERSION', self.get_version())
        config.setdefault('RESTFUL_VERSION', self.get_version(restful=True))
        config.setdefault('TIMEZONE', 'Pacific/Auckland')
        config.setdefault('SHOPIFY_API_SECRET', 'CUSTOM_APP_SECRET')
        config.setdefault('SHOPIFY_API_KEY', 'CUSTOM_APP_KEY')
        config.setdefault('BYPASS_VALIDATE', False)
        config.setdefault('DEBUG', False)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions.setdefault('shopify_utils', self)
        self._config = config

    def get_version(self, version: str = None, restful: bool = False) -> str:
        """ Get API Version """
        # Get Latest version of GraphQL
        today = datetime.today()
        month = int(today.strftime('%-m'))
        for v in [10, 7, 4, 1]:
            if month >= v:
                month = v
                break
        latest_version = int('{}{:02d}'.format(today.strftime('%Y'), month))
        if not version:
            version = self.config.get('API_VERSION', '2023-04') if self.config else '2023-04'
        if version:
            version = int(version.replace('-', ''))
            # check version exists or not
            if version > latest_version:
                version = latest_version
            else:
                # Check deprecate
                if latest_version - 100 > version:
                    version = latest_version
        else:
            version = latest_version
        version = str(version)
        version = '{}-{}'.format(version[:4], version[-2:])
        if restful:
            versions = list(shopify.ApiVersion.versions.keys())
            # unstable version
            if version not in versions:
                version = versions[0]
        return version

        # Admin URL
        # Shopify Default URL
        # Docs URL
        # Customer Data Webhook
