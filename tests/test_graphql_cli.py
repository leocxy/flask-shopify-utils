#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_cli.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 13/07/23 12:02 pm
"""


def test_graphql_cli(initial_test_client) -> None:
    client, test, utils = initial_test_client
    runner = utils.app.test_cli_runner()
    result = runner.invoke(args='generate_schema')
    test.assertEqual(result.exit_code, 1)
