#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 31/03/2025 08:55:10
"""
from flask import Flask, Blueprint, render_template, g
from os.path import join
# custom modules
from app import app_utils

static_folder = join(app_utils.config.get('ROOT_PATH'), 'dist', 'admin')

extension_ui_bp = Blueprint(
    'extension_ui',
    'extension_ui',
    url_prefix='/func',
    template_folder=static_folder,
    static_folder=static_folder,
)


def static_html():
    """ return the same static file """
    return render_template(
        'index.html',
        jwtToken=app_utils.create_admin_jwt_token()
    )


def common_response():
    from flask_shopify_utils.model import Store
    store = Store.query.filter_by(key=g.store_key).first()
    if not store:
        return app_utils.admin_response(400, 'Store not found')
    g.store_id = store.id
    return static_html()


@extension_ui_bp.route('/<extension_name>/create', methods=['GET'], endpoint='extension_create')
@app_utils.check_hmac
def extension_index(extension_name):
    return common_response()


@extension_ui_bp.route('/<extension_name>/<int:record_id>', methods=['GET'], endpoint='extension_edit')
@app_utils.check_hmac
def extension_edit(extension_name, record_id):
    return common_response()


def register_extension_routers(app: Flask) -> None:
    app.register_blueprint(extension_ui_bp)

    from .delivery import delivery_bp
    app.register_blueprint(delivery_bp)
    from .payment import payment_bp
    app.register_blueprint(payment_bp)


__all__ = register_extension_routers
