#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_init.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 11:26 am
"""


def test_init_null_config(utils):
    assert utils.config.get('SHOPIFY_API_SECRET') == 'CUSTOM_APP_SECRET'
    assert utils.config.get('SHOPIFY_API_KEY') == 'CUSTOM_APP_KEY'
    assert utils.config.get('BYPASS_VALIDATE') is 0
    assert utils.config.get('DEBUG') is False
