#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_init.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 11:26 am
"""


def test_init_null_config(initial_test_client) -> None:
    """
    # Because the fixture is "section" scope, so this config could be overwritten by other test case
    :param initial_test_client:
    :return:
    """
    client, test, utils = initial_test_client
    test.assertEqual('CUSTOM_APP_SECRET', utils.config.get('SHOPIFY_API_SECRET'))
    test.assertEqual('CUSTOM_APP_KEY', utils.config.get('SHOPIFY_API_KEY'))
    test.assertEqual(0, utils.config.get('BYPASS_VALIDATE'))
    test.assertEqual(False, utils.config.get('DEBUG'))
