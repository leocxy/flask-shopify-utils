#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : base.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/10/23 4:22 pm
"""
from os import path, getenv
from logging import Formatter, Logger
from logging.handlers import RotatingFileHandler
from functools import wraps
# Request validation
from simplejson import dumps
from sgqlc.operation import Operation
from flask_shopify_utils.utils import GraphQLClient
from flask_shopify_utils.model import Store
from typing import Tuple, Optional
from abc import abstractmethod, ABC
# custom modules
from app import app, db
from app.models.shopify import DiscountCode
from app.schemas.shopify import shopify as shopify_schema


class BasicHelper:
    def __init__(self, store_id: int = 1, log_name: str = 'basic_helper'):
        self._store = Store.query.filter_by(id=store_id).first()
        if not self._store:
            raise Exception('Store[{}] does not exists!'.format(store_id))
        # Shopify API
        self._gql = None
        self._api = None
        self._api_request = None
        # Logger
        self.logger = Logger('BasicHelper')
        handler = RotatingFileHandler(
            path.join(app.config.get('TEMPORARY_PATH'), f'{log_name}.log'),
            maxBytes=5120000,
            backupCount=5
        )
        handler.setFormatter(Formatter('[%(asctime)s] %(threadName)s %(levelname)s:%(message)s'))
        if app.config.get('FLASK_DEBUG', '1') == '1':
            level = 'DEBUG'
            self.logger.addHandler(app.logger.handlers[0])
        else:
            level = 'INFO'
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
        # Shopify Official
        import shopify
        from flask_shopify_utils.utils import patch_shopify_with_limits, get_version
        if not self._api:
            api_session = shopify.Session(self.store.key, get_version(restful=True), self.store.token)
            patch_shopify_with_limits()
            shopify.ShopifyResource.activate_session(api_session)
            self._api = shopify
        return self._api

    @property
    def api_request(self):
        """
        Using requests to send request to Shopify endpoint
        With a better retry strategy and easy to implement to concurrent
        """
        # Using requests
        from requests import Session
        from flask_shopify_utils.utils import initial_restful_adapter
        if not self._api_request:
            self._api_request = Session()
            self._api_request.headers.update({'X-Shopify-Access-Token': self.store.token})
            self._api_request.mount('https://', initial_restful_adapter())
        return self._api_request

    def update_meta(self, owner_id: str, value, namespace: str, key: str, value_type: str = 'json') -> Tuple[
        bool, Optional[str or dict]]:
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
            msg = 'UpdateMeta Error: {}'.format(dumps(res['userErrors']))
            self.logger.warning('UpdateMetaError: %s', msg)
            return False, msg
        return True, res['metafields'][0]['id'].split('/')[-1]


def fn_debug(func):
    """
    debug decorator
    Capture the input and output of the function
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        args[0].logger.debug('Func: {}, Kwargs: {}, Args: {}'.format(func.__name__, kwargs, args[1:]))
        result = func(*args, **kwargs)
        args[0].logger.debug('Func: {}, Result: {}'.format(func.__name__, result))
        return result

    return decorator


class DiscountHelper(ABC, BasicHelper):

    def __init__(self, store_id: int = 1, log_name: str = 'discount_helper', func_name: str = None):
        super(DiscountHelper, self).__init__(store_id, log_name)
        self.func_name = func_name if func_name else 'SHOPIFY_DISCOUNT_ID'
        self._func_id = None
        self._ns = '$app:discount'
        self._key = 'config'
        # Product: 1 << 0
        # Order: 1 << 1
        # Shipping: 1 << 2
        self._code_stamp = 1 << 0
        # DiscountAutomaticNode, DiscountCodeNode
        # gid://shopify/DiscountAutomaticNode/

    @property
    def func_id(self) -> str:
        if not self._func_id:
            self._func_id = getenv(self.func_name, None)
            if self._func_id is None:
                raise Exception('Environment variable[{}] does not exists!'.format(self.func_name))
        return self._func_id

    @staticmethod
    @abstractmethod
    def get_schema() -> dict:
        pass

    @classmethod
    @abstractmethod
    def format_record_data(cls, data: dict) -> Tuple[dict, Optional[dict]]:
        pass

    @abstractmethod
    def format_meta_data(self, data: dict, owner_id: str = None) -> list:
        pass

    @classmethod
    def record_to_dict(cls, record: DiscountCode) -> dict:
        """ You might need to rewrite this method """
        output = dict(
            id=record.code_id,
            type=record.convert_code_type(record.code_type, True),
            code=None,
            title=None,
            message=record.message,
            discount_value=record.discount_value,
            combine_with_product=record.combine_with_product == 1,
            combine_with_order=record.combine_with_order == 1,
            combine_with_shipping=record.combine_with_shipping == 1,
            start_date=record.start_date.strftime('%Y-%m-%dT%H:%M:%S') if record.start_date else None,
            enable_end_date=False,
            end_date=None,
        )
        if record.code_type == 0:
            output['code'] = record.code_name
        else:
            output['title'] = record.code_name
        if record.end_date:
            output['enable_end_date'] = True
            output['end_date'] = record.end_date.strftime('%Y-%m-%dT%H:%M:%S')
        output.update(record.get_extra())
        return output

    def format_discount_code_input_data(self, record: DiscountCode) -> dict:
        input_data = dict(
            title=record.code_name,
            code=record.code_name,
            function_id=self.func_id,
            applies_once_per_customer=record.one_use_per_customer == 1,
            combines_with=dict(
                order_discounts=record.combine_with_order == 1,
                product_discounts=record.combine_with_product == 1,
                shipping_discounts=record.combine_with_shipping == 1,
            ),
            customer_selection=dict(all=True),
            starts_at=record.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        if record.limit_usage == 1 and record.maximum_usage is not None:
            input_data['usage_limit'] = record.maximum_usage
        if record.end_date:
            input_data['ends_at'] = record.end_date.strftime("%Y-%m-%dT%H:%M:%S")
        return input_data

    def format_auto_discount_code_input_data(self, record: DiscountCode) -> dict:
        input_data = dict(
            combines_with=dict(
                order_discounts=record.combine_with_order == 1,
                product_discounts=record.combine_with_product == 1,
                shipping_discounts=record.combine_with_shipping == 1,
            ),
            title=record.code_name,
            function_id=self.func_id,
            starts_at=record.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        if record.end_date:
            input_data['ends_at'] = record.end_date.strftime("%Y-%m-%dT%H:%M:%S")
        return input_data

    def create(self, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        record_data, extra_data = self.format_record_data(data)
        record = DiscountCode.create(
            store_id=self.store.id,
            code_stamp=self._code_stamp,
            **record_data,
        )
        if extra_data:
            record.set_extra(extra_data)
        db.session.flush()

        if record.code_type == 0:
            return self._create_code(record, data)
        return self._create_auto_code(record, data)

    def edit(self, code_id: int) -> Tuple[bool, Optional[str or DiscountCode]]:
        record = DiscountCode.query.filter_by(store_id=self.store.id, code_id=code_id).first()
        if not record:
            return False, f'DiscountNode[{code_id}] does not exists!'
        return True, record

    def update(self, code_id: int, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        rs, record = self.edit(code_id)
        if not rs:
            return False, record, None
        record_data, extra_data = self.format_record_data(data)
        record = DiscountCode.create_or_update(
            dict(store_id=self.store.id, id=record.id),
            **record_data
        )
        if extra_data:
            record.set_extra(extra_data)
        db.session.flush()
        # Check Code Type
        if record.code_type == 0:
            return self._update_code(record, data)
        return self._update_auto_code(record, data)

    def delete(self, code_id: int) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        rs, record = self.edit(code_id)
        if not rs:
            return False, record, None
        if record.code_type == 0:
            return self._delete_code(record)
        return self._delete_auto_code(record)

    def _create_code(self, record: DiscountCode, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        metas = self.format_meta_data(data)
        op = Operation(shopify_schema.mutation_type, 'CreateCode')
        input_data = self.format_discount_code_input_data(record)
        input_data['metafields'] = metas
        mutation = op.discount_code_app_create(code_app_discount=input_data)
        mutation.user_errors()
        mutation.code_app_discount.discount_id()
        res = self.gql.fetch_data(op)['discountCodeAppCreate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('CodeCreateError: %s', msg)
            return False, 'Create discount code failed!', res['userErrors']
        self.logger.debug('CodeCreate: %s', dumps(res))
        record.code_id = res['codeAppDiscount']['discountId'].split('/')[-1]
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _update_code(self, record: DiscountCode, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = Operation(shopify_schema.mutation_type, 'UpdateCode')
        owner_id = 'gid://shopify/DiscountCodeNode/{}'.format(record.code_id)
        input_data = self.format_discount_code_input_data(record)
        mutation = op.discount_code_app_update(
            code_app_discount=input_data,
            id=owner_id
        )
        mutation.user_errors()
        res = self.gql.fetch_data(op)['discountCodeAppUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('CodeUpdateError: %s', msg)
            return False, 'Update discount code failed!', res['userErrors']
        # Update Meta
        metas = self.format_meta_data(data, owner_id)
        op = Operation(shopify_schema.mutation_type, 'UpdateMeta')
        mutation = op.metafields_set(metafields=metas)
        mutation.user_errors()
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateMetaError: %s', msg)
            return False, 'Update discount code failed!', res['userErrors']
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _delete_code(self, record: DiscountCode) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = Operation(shopify_schema.mutation_type, 'DeleteCode')
        mutation = op.discount_code_delete(id='gid://shopify/DiscountCodeNode/{}'.format(record.code_id))
        mutation.user_errors()
        res = self.gql.fetch_data(op)['discountCodeDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('DiscountCodeDeleteError: %s', msg)
            return False, 'Delete discount code failed!', res['userErrors']
        db.session.delete(record)
        db.session.commit()
        return True, None, None

    def _create_auto_code(self, record: DiscountCode, data: dict) -> Tuple[
        bool, Optional[str], Optional[dict or list]]:
        metas = self.format_meta_data(data)
        op = Operation(shopify_schema.mutation_type, 'CreateAutoCode')
        input_data = self.format_auto_discount_code_input_data(record)
        input_data['metafields'] = metas
        mutation = op.discount_automatic_app_create(automatic_app_discount=input_data)
        mutation.user_errors()
        mutation.automatic_app_discount.discount_id()
        res = self.gql.fetch_data(op)['discountAutomaticAppCreate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error(msg)
            return False, 'Create automatic discount code failed!', res['userErrors']
        self.logger.debug('AutomaticCodeCreate: %s', dumps(res))
        record.code_id = res['automaticAppDiscount']['discountId'].split('/')[-1]
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _update_auto_code(self, record: DiscountCode, data: dict) -> Tuple[
        bool, Optional[str], Optional[dict or list]]:
        op = Operation(shopify_schema.mutation_type, 'UpdateAutoCode')
        owner_id = 'gid://shopify/DiscountAutomaticNode/{}'.format(record.code_id)
        input_data = self.format_auto_discount_code_input_data(record)
        mutation = op.discount_automatic_app_update(
            automatic_app_discount=input_data,
            id=owner_id
        )
        mutation.user_errors()
        res = self.gql.fetch_data(op)['discountAutomaticAppUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('AutomaticCodeUpdateError: %s', msg)
            return False, 'Update automatic discount code failed!', res['userErrors']
        # Update Meta
        metas = self.format_meta_data(data, owner_id)
        op = Operation(shopify_schema.mutation_type, 'UpdateMeta')
        mutation = op.metafields_set(metafields=metas)
        mutation.user_errors()
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateMetaError: %s', msg)
            return False, 'Update automatic discount code failed!', res['userErrors']
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _delete_auto_code(self, record: DiscountCode) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = Operation(shopify_schema.mutation_type, 'DeleteCode')
        mutation = op.discount_automatic_delete(id='gid://shopify/DiscountAutomaticNode/{}'.format(record.code_id))
        mutation.user_errors()
        res = self.gql.fetch_data(op)['discountAutomaticDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('AutomaticCodeDeleteError: %s', msg)
            return False, 'Delete automatic discount code failed!', res['userErrors']
        db.session.delete(record)
        db.session.commit()
        return True, None, None
