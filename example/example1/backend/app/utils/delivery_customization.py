#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : delivery_customization.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 31/03/2025 08:56:55
"""
from os import getenv
from simplejson import dumps
# custom modules
from app.utils.base import CustomizationHelper


class DeliveryCustomizationHelper(CustomizationHelper):

    def __init__(self, store_id: int = 1, log_name: str = 'delivery_customization', func_name: str = None) -> None:
        super(DeliveryCustomizationHelper, self).__init__(store_id, log_name)
        self.func_name = func_name if func_name else 'SHOPIFY_DELIVERY_CUSTOMIZATION_ID'
        self._func_id = getenv(self.func_name, None)

        self.customization_type = 'delivery'

        # meta field
        self._ns = '$app:delivery-customization'
        self._key = 'config'
        # self._variables_key = 'variables'

    @staticmethod
    def get_schema() -> dict:
        return dict(
            id=dict(type='integer', required=False, nullable=True),
            title=dict(type='string', required=True),
            enabled=dict(type='boolean', required=True),
            # extra
            attr_key=dict(type='string', required=True),
        )

    def format_metas(self, data: dict, owner_id: str = None) -> list:
        return [dict(
            owner_id=owner_id,
            namespace=self._ns,
            key=self._key,
            type='json',
            value=dumps(dict(attr_key=data['attr_key'])),
        )]


__all__ = DeliveryCustomizationHelper
