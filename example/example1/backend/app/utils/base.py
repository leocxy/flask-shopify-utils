#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : base.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/10/23 4:22 pm
"""
from os import environ, path
from logging import Formatter, Logger
from logging.handlers import RotatingFileHandler
# Request validation
from json import dumps
import shopify
from sgqlc.operation import Operation
from flask_shopify_utils.utils import GraphQLClient, patch_shopify_with_limits, get_version
from flask_shopify_utils.model import Store
# custom modules
from app import app
from app.schemas.shopify import shopify as shopify_schema


class BasicHelper:
    def __init__(self, store_id: int = 1, log_name: str = 'basic_helper'):
        self._store = Store.query.filter_by(id=store_id).first()
        if not self._store:
            raise Exception('Store[{}] does not exists!'.format(store_id))
        # Shopify API
        self._gql = None
        self._api = None
        # Logger
        self.logger = Logger('BasicHelper')
        handler = RotatingFileHandler(
            path.join(app.config.get('TEMPORARY_PATH'), f'{log_name}.log'),
            maxBytes=5120000,
            backupCount=5
        )
        handler.setFormatter(Formatter('[%(asctime)s] %(threadName)s %(levelname)s:%(message)s'))
        if environ.get('FLASK_DEBUG', '1') == '1':
            level = 'DEBUG'
        else:
            level = 'DEBUG'
            self.logger.addHandler(app.logger.handlers[0])
        handler.setLevel(level)
        self.logger.addHandler(handler)

    @property
    def store(self):
        return self._store

    @property
    def gql(self):
        if not self._gql:
            self._gql = GraphQLClient(self.store.key, self.store.token)
        return self._gql

    @property
    def api(self):
        if not self._api:
            api_session = shopify.Session(self.store.key, get_version(restful=True), self.store.token)
            patch_shopify_with_limits()
            shopify.ShopifyResource.activate_session(api_session)
            self._api = shopify
        return self._api

    def update_meta(self, owner_id: str, value, namespace: str, key: str, value_type: str = 'json'):
        op = Operation(shopify_schema.mutation_type, 'UpdateCodeMeta')
        mutation = op.metafields_set(metafields=[dict(
            owner_id=owner_id,
            namespace=namespace,
            key=key,
            type=value_type,
            value=value
        )])
        mutation.user_errors()
        mutation.metafields.id()
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateMetaError: %s', msg)
            return False, res['userErrors']
        return True, res['metafields'][0]['id'].split('/')[-1]
