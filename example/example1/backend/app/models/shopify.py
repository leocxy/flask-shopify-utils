#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : shopify.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/10/23 12:06 pm

Here is an example how to inject function to Store model, since python 3.12, we should do this in another way

from flask_shopify_utils.model import Store
from json import loads, dumps


def set_extra(self, data: dict) -> None:
    extra = self.get_extra()
    extra.update(data)
    self.extra = dumps(extra)


Store.get_extra = lambda self: loads(self.extra) if self.extra else {}
Store.set_extra = set_extra
"""
from flask_shopify_utils.model import BasicMethod, current_time
from simplejson import loads, dumps
# custom models
from app import db


class DiscountCode(db.Model, BasicMethod):
    __tablename__ = 'discount_codes'
    __table_args__ = (
        db.PrimaryKeyConstraint('id'),
        db.Index('store_did', 'store_id', 'code_id')
    )
    id = db.Column(db.Integer)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    code_id = db.Column(db.BigInteger)
    code_stamp = db.Column(db.SmallInteger, comment='0: Product, 1: Order, 2: Shipping')
    code_type = db.Column(db.SmallInteger, default=0, comment="0: Manually, 1: Automatic")
    code_name = db.Column(db.String(255), comment='Code / Title')
    discount_method = db.Column(db.SmallInteger, default=0, comment='0: Fixed, 1: Percentage')
    discount_value = db.Column(db.Integer, comment='Cent / Percentage')
    requirement_type = db.Column(db.String(32))
    requirement_value = db.Column(db.Integer, comment='Cent / Quantity')
    customer_eligibility = db.Column(db.String(32))
    one_use_per_customer = db.Column(db.SmallInteger, default=0)
    limit_usage = db.Column(db.SmallInteger, default=0)
    maximum_usage = db.Column(db.SmallInteger)
    combine_with_product = db.Column(db.SmallInteger, default=0)
    combine_with_order = db.Column(db.SmallInteger, default=0)
    combine_with_shipping = db.Column(db.SmallInteger, default=0)
    start_date = db.Column(db.DateTime, comment='UTC')
    end_date = db.Column(db.DateTime, comment='UTC')
    message = db.Column(db.String(255))
    extra = db.Column(db.Text, comment='JSON')
    created_at = db.Column(db.DateTime, default=current_time)
    updated_at = db.Column(db.DateTime, default=current_time, onupdate=current_time)

    @classmethod
    def convert_code_type(cls, val, revert: bool = False):
        if revert:
            val = int(val)
            return 'code' if val == 0 else 'auto'
        return 0 if val == 'code' else 1

    @classmethod
    def convert_discount_method(cls, val, revert: bool = False):
        if revert:
            val = int(val)
            return 'fixed' if val == 0 else 'percentage'
        return 0 if val == 'fixed' else 1

    def get_extra(self) -> dict:
        return {} if self.extra is None else loads(self.extra)

    def set_extra(self, data: dict) -> dict:
        extra_data = self.get_extra()
        extra_data.update(data)
        self.extra = dumps(extra_data)
        return extra_data

    def to_dict(self) -> dict:
        extra = self.get_extra()
        output = dict(
            id=self.code_id,
            type=self.code_type,
            code=None,
            title=None,
            discount_method=self.discount_method,
            discount_value=self.discount_value,
            requirement_type=self.requirement_type,
            require_amount=None,
            require_quantity=None,
            customer_eligibility=self.customer_eligibility,
            one_use_per_customer=self.one_use_per_customer == 1,
            limit_usage=self.limit_usage == 1,
            maximum_usage=self.maximum_usage,
            combine_with_product=self.combine_with_product == 1,
            combine_with_order=self.combine_with_order == 1,
            combine_with_shipping=self.combine_with_shipping == 1,
            start_date=self.start_date.strftime('%Y-%m-%dT%H:%M:%S') if self.start_date else None,
            enable_end_date=False,
        )
        output.update(**extra)
        if self.code_type == 0:
            output['code'] = self.code_name
        else:
            output['title'] = self.code_name
        if self.end_date:
            output['enable_end_date'] = True
            output['end_date'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S')
        if self.requirement_type == 'total_amount':
            output['require_amount'] = self.requirement_value
        elif self.requirement_type == 'quantity':
            output['require_quantity'] = self.requirement_value
        output['type'] = self.convert_code_type(self.code_type, True)
        if self.discount_method is not None:
            output['discount_method'] = self.convert_discount_method(self.discount_method, True)
        return output
