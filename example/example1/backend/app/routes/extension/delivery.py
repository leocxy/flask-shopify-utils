#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : delivery.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 31/03/2025 08:55:36
"""
from flask import Blueprint, g, request
# custom modules
from app import app_utils
from app.utils.delivery_customization import DeliveryCustomizationHelper

delivery_bp = Blueprint('delivery_custom', __name__, url_prefix='/admin/delivery-customization')


@delivery_bp.route('/create', methods=['POST'], endpoint='delivery_custom_create')
@app_utils.check_jwt
def delivery_custom_create():
    data = request.get_json(silent=True)
    rs, resp = app_utils.form_validate(data, DeliveryCustomizationHelper.get_schema(), True)
    if not rs:
        return resp
    obj = DeliveryCustomizationHelper(g.store_id)
    rs, msg, data = obj.create(data)
    if not rs:
        return app_utils.admin_response(400, msg)
    return app_utils.admin_response(data=data)


@delivery_bp.route('/<int:record_id>', methods=['GET', 'POST', 'DELETE'], endpoint='delivery_custom_edit')
@app_utils.check_jwt
def delivery_custom_edit(record_id):
    obj = DeliveryCustomizationHelper(g.store_id)
    rs, data = obj.edit(record_id)
    if not rs:
        return app_utils.admin_response(400, data)
    if request.method == 'GET':
        return app_utils.admin_response(data=data)
    elif request.method == 'POST':
        data = request.get_json(silent=True)
        rs, resp = app_utils.form_validate(data, DeliveryCustomizationHelper.get_schema(), False)
        if not rs:
            return resp
        rs, msg, data = obj.update(record_id, data)
    else:
        rs, msg, data = obj.delete(record_id)
    if not rs:
        return app_utils.admin_response(400, msg, data)
    return app_utils.admin_response(data=data)


__all__ = delivery_bp
