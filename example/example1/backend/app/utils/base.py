#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : base.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/10/23 4:22 pm
"""
from os import path
from logging import Formatter, Logger
from logging.handlers import RotatingFileHandler
from functools import wraps
# Request validation
from simplejson import dumps
from flask_shopify_utils.utils import GraphQLClient
from flask_shopify_utils.model import Store
from typing import Tuple, Optional
from abc import abstractmethod, ABC
# custom modules
from app import app, db
from app.models.shopify import DiscountCode
from app.schemas.query import query_delivery_customization, query_payment_customization
from app.schemas.mutation import update_meta, create_discount_code, update_discount_code, \
    delete_discount_code, create_auto_discount, update_auto_discount, delete_auto_discount, \
    update_multiple_meta, create_delivery_customization, update_delivery_customization, \
    delete_delivery_customization, create_payment_customization, update_payment_customization, \
    delete_payment_customization

###
# Add custom methods here
###


# inherit from example code

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


class BasicHelper:
    def __init__(self, store_id: int = 1, log_name: str = 'basic_helper'):
        self._store = Store.query.filter_by(id=store_id).first()
        if not self._store:
            raise Exception('Store[{}] does not exists!'.format(store_id))
        # Shopify API
        self._gql = None
        self._restful = None
        # Logger
        self.logger = Logger('BasicHelper')
        handler = RotatingFileHandler(
            path.join(app.config.get('TEMPORARY_PATH'), f'{log_name}.log'),
            # 10 MB
            maxBytes=10240000,
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
    def gql(self, cost_debug: bool = False):
        if not self._gql:
            self._gql = GraphQLClient(self.store.key, self.store.token, cost_debug=cost_debug)
        return self._gql

    @fn_debug
    def restful(self, url_path: str, method: str = 'GET', params: dict = None, json_data: dict = None):
        """
        Restful API has been deprecated by Shopify Since 2024-10-01

        Using requests to send request to Shopify endpoint
        With a better retry strategy and easy to implement to concurrent
        # pagination
        https://shopify.dev/docs/api/admin-rest/usage/pagination

        ### example
        # get customers data
        ```python
        res = self.restful('customers', 'GET')
        ```
        """
        # Using requests
        from requests import Session
        from flask_shopify_utils.utils import initial_restful_adapter, get_version
        if not self._restful:
            self._restful = Session()
            self._restful.headers.update({'X-Shopify-Access-Token': self.store.token})
            self._restful.mount('https://', initial_restful_adapter())

        # build the full URL
        url = f'https://{self.store.key}/admin/api/{get_version()}/{url_path}.json'
        # this might have some issue
        return self._restful.request(method.upper(), url, params=params, json=json_data)

    def update_meta(self, owner_id: str, value, namespace: str, key: str, value_type: str = 'json') \
            -> Tuple[bool, Optional[str or dict]]:
        op = update_meta(owner_id, value, namespace, key, value_type)
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = 'UpdateMeta Error: {}'.format(dumps(res['userErrors']))
            self.logger.warning('UpdateMetaError: %s', msg)
            return False, msg
        return True, res['metafields'][0]['id'].split('/')[-1]


class DiscountHelper(ABC, BasicHelper):
    """ Here is the abstract class for DiscountCode """

    def __init__(self, store_id: int = 1, log_name: str = 'discount_helper'):
        super(DiscountHelper, self).__init__(store_id, log_name)
        # grab this from extensions/??/shopify.extension.toml
        self._func_handle = None
        self._ns = '$app:discount'
        self._key = 'config'
        # Product: 1 << 0
        # Order: 1 << 1
        # Shipping: 1 << 2
        self._code_stamp = 1 << 0
        # DiscountAutomaticNode, DiscountCodeNode
        # gid://shopify/DiscountAutomaticNode/

    @property
    def func_handle(self) -> str:
        if not self._func_handle:
            # need to use to function handle to create the discount code
            raise Exception('Function handle is not set!')
        return self._func_handle

    @staticmethod
    @abstractmethod
    def get_schema() -> dict:
        """
        Schema example

        date_regex = r'^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$'
        return dict(
            type=dict(type='string', required=True, allowed=['auto']),
            code=dict(type='string', required=True, nullable=True, maxlength=32),
            title=dict(type='string', required=True, nullable=True, maxlength=64),
            message=dict(type='string', required=True, nullable=True, maxlength=255),
            combine_with_product=dict(type='boolean', required=True),
            combine_with_order=dict(type='boolean', required=True),
            combine_with_shipping=dict(type='boolean', required=True),
            start_date=dict(type='string', required=True, regex=date_regex),
            enable_end_date=dict(type='boolean', required=True),
            end_date=dict(type='string', required=True, regex=date_regex, nullable=True),
            # extra add here
        )
        """
        pass

    @classmethod
    @abstractmethod
    def format_record_data(cls, data: dict) -> Tuple[dict, Optional[dict]]:
        """
        Example

        code_type = DiscountCode.convert_code_type(data['type'])
        return dict(
            code_type=code_type,
            code_name=data['code'] if code_type == 0 else data['title'],
            message=data.get('message', None),
            discount_method=None,
            discount_value=data.get('discount_value', None),
            requirement_type=None,
            requirement_value=None,
            customer_eligibility=None,
            one_use_per_customer=None,
            limit_usage=None,
            maximum_usage=None,
            combine_with_order=1 if data['combine_with_order'] else 0,
            combine_with_product=1 if data['combine_with_product'] else 0,
            combine_with_shipping=1 if data['combine_with_shipping'] else 0,
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%S'),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%dT%H:%M:%S') if data['enable_end_date'] else None,
        ), None
        """
        pass

    @abstractmethod
    def format_meta_data(self, data: dict, owner_id: str = None) -> list:
        """
        Example

        return [dict(
            owner_id=owner_id,
            namespace=self._ns,
            key=self._key,
            type='json',
            value=dumps(dict(
                message=data['message'],
                # extra add here
            ))
        )]
        """
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
            discount_method=None if record.discount_method is None else record.convert_discount_method(
                record.discount_method, True),
            discount_value=record.discount_value,
            requirement_type=record.requirement_type,
            requirement_value=record.requirement_value,
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
        # load extra data
        output.update(record.get_extra())
        return output

    def get_discount_classes(self) -> list:
        rs = []
        if self._code_stamp & (1 << 0):
            rs.append('PRODUCT')
        if self._code_stamp & (1 << 1):
            rs.append('ORDER')
        if self._code_stamp & (1 << 2):
            rs.append('SHIPPING')
        return rs

    def format_discount_code_input_data(self, record: DiscountCode) -> dict:
        input_data = dict(
            title=record.code_name,
            code=record.code_name,
            function_handle=self.func_handle,
            applies_once_per_customer=record.one_use_per_customer == 1,
            combines_with=dict(
                order_discounts=record.combine_with_order == 1,
                product_discounts=record.combine_with_product == 1,
                shipping_discounts=record.combine_with_shipping == 1,
            ),
            customer_selection=dict(all=True),
            starts_at=record.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            discount_classes=self.get_discount_classes(),
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
            function_handle=self.func_handle,
            starts_at=record.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            discount_classes=self.get_discount_classes(),
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

    def update_metas(self, data: dict, owner_id: str) -> Tuple[bool, Optional[str], Optional[list]]:
        op = update_multiple_meta(self.format_meta_data(data, owner_id))
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('MetaUpdateError: %s', msg)
            return False, 'Update code metas failed!', res['userErrors']
        return True, None, None

    def _create_code(self, record: DiscountCode, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        metas = self.format_meta_data(data)
        input_data = self.format_discount_code_input_data(record)
        input_data['metafields'] = metas
        op = create_discount_code(input_data)
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
        owner_id = 'gid://shopify/DiscountCodeNode/{}'.format(record.code_id)
        input_data = self.format_discount_code_input_data(record)
        op = update_discount_code(owner_id, input_data)
        res = self.gql.fetch_data(op)['discountCodeAppUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('CodeUpdateError: %s', msg)
            return False, 'Update discount code failed!', res['userErrors']

        # meta update
        rs, msg, err = self.update_metas(data, owner_id)
        if not rs:
            return False, msg, err
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _delete_code(self, record: DiscountCode) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = delete_discount_code(record.code_id)
        res = self.gql.fetch_data(op)['discountCodeDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('DiscountCodeDeleteError: %s', msg)
            return False, 'Delete discount code failed!', res['userErrors']
        db.session.delete(record)
        db.session.commit()
        return True, None, None

    def _create_auto_code(self, record: DiscountCode, data: dict) \
            -> Tuple[bool, Optional[str], Optional[dict or list]]:
        metas = self.format_meta_data(data)
        input_data = self.format_auto_discount_code_input_data(record)
        input_data['metafields'] = metas
        op = create_auto_discount(input_data)
        res = self.gql.fetch_data(op)['discountAutomaticAppCreate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error(msg)
            return False, 'Create automatic discount code failed!', res['userErrors']
        self.logger.debug('AutomaticCodeCreate: %s', dumps(res))
        record.code_id = res['automaticAppDiscount']['discountId'].split('/')[-1]
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _update_auto_code(self, record: DiscountCode, data: dict) \
            -> Tuple[bool, Optional[str], Optional[dict or list]]:
        owner_id = 'gid://shopify/DiscountAutomaticNode/{}'.format(record.code_id)
        input_data = self.format_auto_discount_code_input_data(record)
        op = update_auto_discount(owner_id, input_data)
        res = self.gql.fetch_data(op)['discountAutomaticAppUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('AutomaticCodeUpdateError: %s', msg)
            return False, 'Update automatic discount code failed!', res['userErrors']

        # meta update
        rs, msg, err = self.update_metas(data, owner_id)
        if not rs:
            return False, msg, err
        db.session.commit()
        return True, None, self.record_to_dict(record)

    def _delete_auto_code(self, record: DiscountCode) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = delete_auto_discount(record.code_id)
        res = self.gql.fetch_data(op)['discountAutomaticDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('AutomaticCodeDeleteError: %s', msg)
            return False, 'Delete automatic discount code failed!', res['userErrors']
        db.session.delete(record)
        db.session.commit()
        return True, None, None


class CustomizationHelper(ABC, BasicHelper):
    """ Here is the abstract class for Customization function """

    def __init__(self, store_id: int = 1, log_name: str = 'customization') -> None:
        """ this method should be override by the subclass """
        super(CustomizationHelper, self).__init__(store_id, log_name)
        # grab this from extensions/??/shopify.extension.toml
        self._func_handle = None

        # it should be 'payment or 'delivery'
        self.customization_type = 'payment'

        # meta field
        self._ns = '$app:{}-customization'.format(self.customization_type)
        self._key = 'config'
        # self._variables_key = 'variables'

    @property
    def func_handle(self) -> str:
        if not self._func_handle:
            # need to use to function handle to create the discount code
            raise Exception('Function handle is not set!')
        return self._func_handle

    @staticmethod
    @abstractmethod
    def get_schema() -> dict:
        """
        Schema example

        return dict(
            id=dict(type='integer', required=False, nullable=True),
            title=dict(type='string', required=True),
            enabled=dict(type='boolean', required=True),
            # extra data ...
        )
        """

    @abstractmethod
    def format_metas(self, data: dict, owner_id: str = None) -> list:
        """
        Example

        return [dict(
            owner_id=owner_id,
            namespace=self._ns,
            key=self._key,
            type='json',
            value=dumps(data),
        )]
        """

    def edit(self, record_id: int) -> Tuple[bool, Optional[dict or str]]:
        """ dynamic call the method based on the customization type """
        fn = getattr(self, f'{self.customization_type}_edit')
        return fn(record_id)

    def create(self, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        """ dynamic call the method based on the customization type """
        fn = getattr(self, f'{self.customization_type}_create')
        return fn(data)

    def update(self, record_id: int, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        """ dynamic call the method based on the customization type """
        fn = getattr(self, f'{self.customization_type}_update')
        return fn(record_id, data)

    def delete(self, record_id: int) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        """ dynamic call the method based on the customization type """
        fn = getattr(self, f'{self.customization_type}_delete')
        return fn(record_id)

    def delivery_edit(self, record_id: int) -> Tuple[bool, Optional[dict or str]]:
        gid = f'gid://shopify/DeliveryCustomization/{record_id}'
        op = query_delivery_customization(gid, self._ns, self._key)
        res = self.gql.fetch_data(op)['deliveryCustomization']
        self.logger.info('QueryDeliveryCustomizationSuccess: %s', dumps(res))
        if not res:
            return False, 'Record not found!'
        result = dict(
            id=record_id,
            enabled=res['enabled'],
            title=res['title']
        )
        if meta := res['metafield']:
            result.update(meta['jsonValue'])
        return True, result

    def delivery_create(self, data: dict) -> Tuple[bool, Optional[str], Optional[list or dict]]:
        metas = self.format_metas(data)
        op = create_delivery_customization(dict(
            function_handle=self.func_handle,
            enabled=data['enabled'],
            title=data['title'],
            metafields=metas
        ))
        res = self.gql.fetch_data(op)['deliveryCustomizationCreate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('CreateDeliveryCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('CreateDeliveryCustomizationSuccess: %s', dumps(res))
        return True, None, dict(
            id=int(res['deliveryCustomization']['id'].split('/')[-1]),
            title=data['title'],
            enabled=data['enabled'],
        )

    def delivery_update(self, record_id: int, data: dict) -> Tuple[bool, Optional[str], Optional[dict or str]]:
        gid = f'gid://shopify/DeliveryCustomization/{record_id}'
        op = update_delivery_customization(gid, dict(
            enabled=data['enabled'],
            title=data['title'],
        ))
        res = self.gql.fetch_data(op)['deliveryCustomizationUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateDeliveryCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('UpdateDeliveryCustomizationSuccess: %s', dumps(res))
        # Update Meta
        metas = self.format_metas(data, gid)
        op = update_multiple_meta(metas)
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateDeliveryCustomizationMetaError: %s', msg)
            return False, msg, res['userErrors']
        return True, None, dict(
            id=record_id,
            enabled=data['enabled'],
            title=data['title']
        )

    def delivery_delete(self, record_id: int) -> Tuple[bool, Optional[str], Optional[list]]:
        gid = f'gid://shopify/DeliveryCustomization/{record_id}'
        op = delete_delivery_customization(gid)
        res = self.gql.fetch_data(op)['deliveryCustomizationDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('DeleteDeliveryCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('DeleteDeliveryCustomizationSuccess: %s', record_id)
        return True, None, None

    def payment_edit(self, record_id: int) -> Tuple[bool, Optional[dict or str]]:
        gid = f'gid://shopify/PaymentCustomization/{record_id}'
        op = query_payment_customization(gid, self._ns, self._key)
        res = self.gql.fetch_data(op)['paymentCustomization']
        self.logger.info('QueryPaymentCustomizationSuccess: %s', dumps(res))
        if not res:
            return False, 'Record not found!'
        result = dict(
            id=record_id,
            enabled=res['enabled'],
            title=res['title']
        )
        if meta := res['metafield']:
            result.update(meta['jsonValue'])
        return True, result

    def payment_create(self, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        op = create_payment_customization(dict(
            function_handle=self.func_handle,
            enabled=data['enabled'],
            title=data['title'],
            metafields=self.format_metas(data)
        ))
        res = self.gql.fetch_data(op)['paymentCustomizationCreate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('CreatePaymentCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('CreatePaymentCustomizationSuccess: %s', dumps(res))
        return True, None, dict(
            id=int(res['paymentCustomization']['id'].split('/')[-1]),
            enabled=data['enabled'],
            title=data['title'],
        )

    def payment_update(self, record_id: int, data: dict) -> Tuple[bool, Optional[str], Optional[dict or list]]:
        gid = f'gid://shopify/PaymentCustomization/{record_id}'
        op = update_payment_customization(gid, dict(
            enabled=data['enabled'],
            title=data['title'],
        ))
        res = self.gql.fetch_data(op)['paymentCustomizationUpdate']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdatePaymentCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('UpdatePaymentCustomizationSuccess: %s', dumps(res))
        # Update meta
        metas = self.format_metas(data, gid)
        op = update_multiple_meta(metas)
        res = self.gql.fetch_data(op)['metafieldsSet']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('UpdateMetaError: %s', msg)
            return False, msg, res['userErrors']
        return True, None, dict(
            id=record_id,
            enabled=data['enabled'],
            title=data['title'],
        )

    def payment_delete(self, record_id: int) -> Tuple[bool, Optional[str], Optional[list]]:
        gid = f'gid://shopify/PaymentCustomization/{record_id}'
        op = delete_payment_customization(gid)
        res = self.gql.fetch_data(op)['paymentCustomizationDelete']
        if len(res['userErrors']) > 0:
            msg = dumps(res['userErrors'])
            self.logger.error('DeletePaymentCustomizationError: %s', msg)
            return False, msg, res['userErrors']
        self.logger.info('DeletePaymentCustomizationSuccess: %s', record_id)
        return True, None, None
