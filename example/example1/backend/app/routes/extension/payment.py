#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : payment.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 31/03/2025 08:55:51
"""
from flask import Blueprint, g, request
# custom modules
from app import app_utils
from app.utils.payment_customization import PaymentCustomizationHelper

payment_bp = Blueprint('payment_custom', __name__, url_prefix='/admin/payment-customization')


@payment_bp.route('/create', methods=['POST'], endpoint='payment_custom_create')
@app_utils.check_jwt
def payment_custom_create():
    data = request.get_json(silent=True)
    rs, res = app_utils.form_validate(data, PaymentCustomizationHelper.get_schema(), True)
    if not rs:
        return res
    obj = PaymentCustomizationHelper(g.store_id)
    rs, msg, data = obj.create(data)
    if not rs:
        return app_utils.admin_response(400, msg)
    return app_utils.admin_response(data=data)


@payment_bp.route('/<int:record_id>', methods=['GET', 'POST', 'DELETE'], endpoint='payment_custom_edit')
@app_utils.check_jwt
def payment_custom_edit(record_id):
    obj = PaymentCustomizationHelper(g.store_id)
    rs, data = obj.edit(record_id)
    if not rs:
        return app_utils.admin_response(400, data)
    if request.method == 'GET':
        return app_utils.admin_response(data=data)
    elif request.method == 'POST':
        data = request.get_json(silent=True)
        rs, res = app_utils.form_validate(data, PaymentCustomizationHelper.get_schema(), False)
        if not rs:
            return res
        rs, msg, data = obj.update(record_id, data)
    else:
        rs, msg, data = obj.delete(record_id)
    if not rs:
        return app_utils.admin_response(400, msg, data)
    return app_utils.admin_response(data=data)


__all__ = payment_bp
