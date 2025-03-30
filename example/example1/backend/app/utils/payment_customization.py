#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : payment_customization.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 31/03/2025 08:56:28
"""
from os import getenv
from simplejson import dumps
# custom modules
from app.utils.base import CustomizationHelper


class PaymentCustomizationHelper(CustomizationHelper):
    def __init__(self, store_id: int = 1, log_name: str = 'payment_customization', func_name: str = None) -> None:
        super(PaymentCustomizationHelper, self).__init__(store_id, log_name)
        self.func_name = func_name if func_name else 'SHOPIFY_PAYMENT_CUSTOMIZATION_ID'
        self._func_id = getenv(self.func_name, None)

        self.customization_type = 'payment'

        # meta field
        self._ns = '$app:payment-customization'
        self._key = 'config'
        # self._variables_key = 'variables'

    @staticmethod
    def get_schema() -> dict:
        return dict(
            id=dict(type='integer', required=False, nullable=True),
            title=dict(type='string', required=True, min=5, max=50),
            enabled=dict(type='boolean', required=True),
            # extra
            destination=dict(type='string', required=True, allowed=['NZ']),
            # payment method name, case sensitive
            methods=dict(type='list', required=True, schema=dict(
                type='string', required=True, maxlength=255
            ))
        )

    def format_metas(self, data: dict, owner_id: str = None) -> list:
        return [dict(
            owner_id=owner_id,
            namespace=self._ns,
            key=self._key,
            type='json',
            value=dumps(dict(
                destination=data['destination'],
                methods=data['methods'],
            )),
        )]
