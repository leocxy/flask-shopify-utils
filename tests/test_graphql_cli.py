#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_cli.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 13/07/23 12:02 pm
"""


def test_graphql_cli(utils):
    utils.enroll_graphql_schema_cli()
    runner = utils.app.test_cli_runner()
    result = runner.invoke(args='generate_schema')
    assert result.exit_code == 1
